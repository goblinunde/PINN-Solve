use ndarray::{Array1, Array2};
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

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
