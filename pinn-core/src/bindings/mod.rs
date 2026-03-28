use aes_gcm::aead::{Aead, KeyInit};
use aes_gcm::{Aes256Gcm, Nonce};
use base64::engine::general_purpose::STANDARD;
use base64::Engine;
use ndarray::{Array1, Array2};
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use rand::RngCore;
use std::fs;
use std::path::PathBuf;

use crate::solver::{PDESolver as RustSolver, SolverConfig};

#[pyclass]
pub struct Network {
    layers: Vec<usize>,
}

#[pymethods]
impl Network {
    #[new]
    fn new(layers: Vec<usize>) -> Self {
        Self { layers }
    }
    
    fn get_layers(&self) -> Vec<usize> {
        self.layers.clone()
    }
}

#[pyclass]
pub struct Solver {
    solver: RustSolver,
}

fn parse_solver_config(config_json: &str) -> PyResult<SolverConfig> {
    serde_json::from_str(config_json)
        .map_err(|error| PyValueError::new_err(format!("Invalid solver config: {error}")))
}

fn secret_key_path() -> PyResult<PathBuf> {
    let base_dir = dirs::config_dir()
        .ok_or_else(|| PyValueError::new_err("Unable to locate config directory for Rust secret manager"))?;
    Ok(base_dir.join("pinn-solve").join("master.key"))
}

fn load_or_create_secret_key() -> PyResult<[u8; 32]> {
    let key_path = secret_key_path()?;
    if let Some(parent) = key_path.parent() {
        fs::create_dir_all(parent)
            .map_err(|error| PyValueError::new_err(format!("Unable to prepare secret key directory: {error}")))?;
    }

    if key_path.exists() {
        let encoded = fs::read_to_string(&key_path)
            .map_err(|error| PyValueError::new_err(format!("Unable to read Rust secret key: {error}")))?;
        let decoded = STANDARD
            .decode(encoded.trim())
            .map_err(|error| PyValueError::new_err(format!("Unable to decode Rust secret key: {error}")))?;
        let key: [u8; 32] = decoded
            .try_into()
            .map_err(|_| PyValueError::new_err("Rust secret key must be 32 bytes"))?;
        return Ok(key);
    }

    let mut key = [0u8; 32];
    rand::thread_rng().fill_bytes(&mut key);
    let encoded = STANDARD.encode(key);
    fs::write(&key_path, encoded)
        .map_err(|error| PyValueError::new_err(format!("Unable to persist Rust secret key: {error}")))?;
    Ok(key)
}

fn encrypt_secret_impl(value: &str) -> PyResult<String> {
    let key = load_or_create_secret_key()?;
    let cipher = Aes256Gcm::new_from_slice(&key)
        .map_err(|error| PyValueError::new_err(format!("Unable to initialize Rust cipher: {error}")))?;

    let mut nonce_bytes = [0u8; 12];
    rand::thread_rng().fill_bytes(&mut nonce_bytes);
    let nonce = Nonce::from_slice(&nonce_bytes);
    let ciphertext = cipher
        .encrypt(nonce, value.as_bytes())
        .map_err(|error| PyValueError::new_err(format!("Rust encryption failed: {error}")))?;

    Ok(format!(
        "rust-aes256:{}:{}",
        STANDARD.encode(nonce_bytes),
        STANDARD.encode(ciphertext)
    ))
}

fn decrypt_secret_impl(value: &str) -> PyResult<String> {
    if !value.starts_with("rust-aes256:") {
        return Ok(value.to_string());
    }

    let parts: Vec<&str> = value.splitn(3, ':').collect();
    if parts.len() != 3 {
        return Err(PyValueError::new_err("Invalid Rust-encrypted secret format"));
    }

    let key = load_or_create_secret_key()?;
    let cipher = Aes256Gcm::new_from_slice(&key)
        .map_err(|error| PyValueError::new_err(format!("Unable to initialize Rust cipher: {error}")))?;
    let nonce_bytes = STANDARD
        .decode(parts[1])
        .map_err(|error| PyValueError::new_err(format!("Unable to decode Rust nonce: {error}")))?;
    let ciphertext = STANDARD
        .decode(parts[2])
        .map_err(|error| PyValueError::new_err(format!("Unable to decode Rust ciphertext: {error}")))?;

    let plaintext = cipher
        .decrypt(Nonce::from_slice(&nonce_bytes), ciphertext.as_ref())
        .map_err(|error| PyValueError::new_err(format!("Rust decryption failed: {error}")))?;

    String::from_utf8(plaintext)
        .map_err(|error| PyValueError::new_err(format!("Decrypted secret is not valid UTF-8: {error}")))
}

#[pymethods]
impl Solver {
    #[new]
    fn new(layers: Vec<usize>, learning_rate: f64) -> Self {
        Self {
            solver: RustSolver::new(layers, learning_rate),
        }
    }

    fn train(&mut self, x_data: Vec<Vec<f64>>, epochs: usize, n_boundary: usize) -> PyResult<Vec<f64>> {
        if x_data.is_empty() {
            return Err(PyValueError::new_err("x_data must not be empty"));
        }

        let rows = x_data.len();
        let cols = x_data[0].len();
        if cols == 0 {
            return Err(PyValueError::new_err("x_data rows must not be empty"));
        }

        if x_data.iter().any(|row| row.len() != cols) {
            return Err(PyValueError::new_err("x_data rows must all have the same length"));
        }

        let flat: Vec<f64> = x_data.into_iter().flatten().collect();
        let array = Array2::from_shape_vec((rows, cols), flat)
            .map_err(|error| PyValueError::new_err(format!("Invalid training data shape: {error}")))?;

        Ok(self.solver.train(&array, epochs, n_boundary))
    }

    fn predict(&self, x: Vec<f64>) -> f64 {
        let input = Array1::from_vec(x);
        self.solver.predict(&input)
    }

    fn predict_batch(&self, x_data: Vec<Vec<f64>>) -> Vec<f64> {
        x_data
            .into_iter()
            .map(|x| {
                let input = Array1::from_vec(x);
                self.solver.predict(&input)
            })
            .collect()
    }
}

#[pyfunction]
pub fn create_solver_from_config_json(config_json: &str) -> PyResult<Solver> {
    let config = parse_solver_config(config_json)?;
    Ok(Solver {
        solver: RustSolver::from_config(config),
    })
}

#[pyfunction]
pub fn encrypt_secret(value: &str) -> PyResult<String> {
    encrypt_secret_impl(value)
}

#[pyfunction]
pub fn decrypt_secret(value: &str) -> PyResult<String> {
    decrypt_secret_impl(value)
}
