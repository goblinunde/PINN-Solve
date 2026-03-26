use std::f64::consts::PI;

use ndarray::{Array1, Array2, Axis};
use rand::seq::SliceRandom;
use rand::Rng;
use serde::{Deserialize, Serialize};

use crate::autodiff::{compute_derivative, compute_second_derivative};
use crate::nn::{Network, NetworkConfig, Optimizer, OptimizerKind};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub enum PDEKind {
    #[serde(rename = "laplace_2d")]
    Laplace2D,
    #[serde(rename = "poisson_2d")]
    Poisson2D,
    #[serde(rename = "heat_1d")]
    Heat1D,
    #[serde(rename = "burgers_1d")]
    Burgers1D,
}

impl Default for PDEKind {
    fn default() -> Self {
        Self::Laplace2D
    }
}

impl PDEKind {
    pub fn input_dim(&self) -> usize {
        2
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum SourceType {
    Zero,
    One,
    Sine,
}

impl Default for SourceType {
    fn default() -> Self {
        Self::Zero
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct PDEConfig {
    #[serde(default)]
    pub kind: PDEKind,
    #[serde(default)]
    pub source_type: SourceType,
    #[serde(default = "default_alpha")]
    pub alpha: f64,
    #[serde(default = "default_viscosity")]
    pub viscosity: f64,
}

impl Default for PDEConfig {
    fn default() -> Self {
        Self {
            kind: PDEKind::default(),
            source_type: SourceType::default(),
            alpha: default_alpha(),
            viscosity: default_viscosity(),
        }
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct SolverConfig {
    #[serde(default)]
    pub network: NetworkConfig,
    #[serde(default)]
    pub optimizer: OptimizerKind,
    #[serde(default = "default_learning_rate")]
    pub learning_rate: f64,
    #[serde(default)]
    pub pde: PDEConfig,
    #[serde(default = "default_epsilon")]
    pub epsilon: f64,
    #[serde(default = "default_lambda_boundary")]
    pub lambda_boundary: f64,
    #[serde(default = "default_collocation_batch_size")]
    pub collocation_batch_size: usize,
}

fn default_learning_rate() -> f64 {
    1e-3
}

fn default_alpha() -> f64 {
    0.1
}

fn default_viscosity() -> f64 {
    0.01
}

fn default_epsilon() -> f64 {
    1e-4
}

fn default_lambda_boundary() -> f64 {
    10.0
}

fn default_collocation_batch_size() -> usize {
    64
}

impl Default for SolverConfig {
    fn default() -> Self {
        Self {
            network: NetworkConfig::default(),
            optimizer: OptimizerKind::default(),
            learning_rate: default_learning_rate(),
            pde: PDEConfig::default(),
            epsilon: default_epsilon(),
            lambda_boundary: default_lambda_boundary(),
            collocation_batch_size: default_collocation_batch_size(),
        }
    }
}

impl SolverConfig {
    pub fn from_legacy(layer_sizes: &[usize], learning_rate: f64) -> Self {
        let mut config = Self::default();
        config.network = NetworkConfig::from_layer_sizes(layer_sizes);
        config.learning_rate = learning_rate;
        config.normalize()
    }

    pub fn normalize(mut self) -> Self {
        self.network.input_dim = self.pde.kind.input_dim();
        self.network.output_dim = 1;
        self.collocation_batch_size = self.collocation_batch_size.max(1);
        self.epsilon = self.epsilon.max(1e-6);
        self.lambda_boundary = self.lambda_boundary.max(0.0);
        self
    }
}

pub struct PDESolver {
    network: Network,
    optimizer: Optimizer,
    config: SolverConfig,
}

impl PDESolver {
    pub fn new(layer_sizes: Vec<usize>, learning_rate: f64) -> Self {
        Self::from_config(SolverConfig::from_legacy(&layer_sizes, learning_rate))
    }

    pub fn from_config(config: SolverConfig) -> Self {
        let normalized = config.normalize();
        let network = Network::from_config(normalized.network.clone());
        let optimizer = Optimizer::new(normalized.optimizer.clone(), &network, normalized.learning_rate);

        Self {
            network,
            optimizer,
            config: normalized,
        }
    }

    fn pde_output(&self, point: &Array1<f64>) -> f64 {
        self.network.infer(point)[0]
    }

    fn source_term(&self, point: &Array1<f64>) -> f64 {
        match self.config.pde.source_type {
            SourceType::Zero => 0.0,
            SourceType::One => 1.0,
            SourceType::Sine => (PI * point[0]).sin() * (PI * point[1]).sin(),
        }
    }

    fn initial_condition(&self, x: f64) -> f64 {
        match self.config.pde.kind {
            PDEKind::Heat1D => (PI * x).sin(),
            PDEKind::Burgers1D => -(PI * x).sin(),
            _ => 0.0,
        }
    }

    fn residual_at(&self, point: &Array1<f64>) -> f64 {
        let epsilon = self.config.epsilon;
        let output = |input: &Array1<f64>| self.pde_output(input);

        match self.config.pde.kind {
            PDEKind::Laplace2D => {
                let u_xx = compute_second_derivative(&output, point, 0, epsilon);
                let u_yy = compute_second_derivative(&output, point, 1, epsilon);
                u_xx + u_yy
            }
            PDEKind::Poisson2D => {
                let u_xx = compute_second_derivative(&output, point, 0, epsilon);
                let u_yy = compute_second_derivative(&output, point, 1, epsilon);
                u_xx + u_yy - self.source_term(point)
            }
            PDEKind::Heat1D => {
                let u_t = compute_derivative(&output, point, 1, epsilon);
                let u_xx = compute_second_derivative(&output, point, 0, epsilon);
                u_t - self.config.pde.alpha * u_xx
            }
            PDEKind::Burgers1D => {
                let u = output(point);
                let u_t = compute_derivative(&output, point, 1, epsilon);
                let u_x = compute_derivative(&output, point, 0, epsilon);
                let u_xx = compute_second_derivative(&output, point, 0, epsilon);
                u_t + u * u_x - self.config.pde.viscosity * u_xx
            }
        }
    }

    pub fn compute_pde_residual(&self, x: &Array2<f64>) -> f64 {
        if x.nrows() == 0 {
            return 0.0;
        }

        let mut total = 0.0;
        for row in x.rows() {
            let residual = self.residual_at(&row.to_owned());
            total += residual * residual;
        }

        total / x.nrows() as f64
    }

    pub fn compute_boundary_loss(&self, x_boundary: &Array2<f64>, u_boundary: &Array1<f64>) -> f64 {
        if x_boundary.nrows() == 0 {
            return 0.0;
        }

        let mut total = 0.0;
        for index in 0..x_boundary.nrows() {
            let prediction = self.pde_output(&x_boundary.row(index).to_owned());
            let diff = prediction - u_boundary[index];
            total += diff * diff;
        }

        total / x_boundary.nrows() as f64
    }

    fn sample_collocation_batch(&self, x_data: &Array2<f64>) -> Array2<f64> {
        if x_data.nrows() <= self.config.collocation_batch_size {
            return x_data.clone();
        }

        let mut rng = rand::thread_rng();
        let mut indices: Vec<usize> = (0..x_data.nrows()).collect();
        indices.shuffle(&mut rng);
        indices.truncate(self.config.collocation_batch_size);
        x_data.select(Axis(0), &indices)
    }

    fn generate_fallback_collocation_points(&self, n_points: usize) -> Array2<f64> {
        let count = n_points.max(self.config.collocation_batch_size);
        let mut rng = rand::thread_rng();
        let dims = self.config.pde.kind.input_dim();
        let values: Vec<f64> = (0..count * dims).map(|_| rng.gen::<f64>()).collect();
        Array2::from_shape_vec((count, dims), values).unwrap()
    }

    fn prepare_collocation_points(&self, x_data: &Array2<f64>) -> Array2<f64> {
        if x_data.nrows() == 0 || x_data.ncols() != self.config.pde.kind.input_dim() {
            self.generate_fallback_collocation_points(128)
        } else {
            x_data.clone()
        }
    }

    fn generate_boundary_conditions(&self, n_boundary: usize) -> (Array2<f64>, Array1<f64>) {
        let count = n_boundary.max(8);
        let mut rng = rand::thread_rng();
        let mut points = Vec::with_capacity(count * self.config.pde.kind.input_dim());
        let mut values = Vec::with_capacity(count);

        match self.config.pde.kind {
            PDEKind::Laplace2D | PDEKind::Poisson2D => {
                for _ in 0..count {
                    let side = rng.gen_range(0..4);
                    let t = rng.gen::<f64>();
                    let (x, y) = match side {
                        0 => (0.0, t),
                        1 => (1.0, t),
                        2 => (t, 0.0),
                        _ => (t, 1.0),
                    };
                    points.extend([x, y]);
                    values.push(0.0);
                }
            }
            PDEKind::Heat1D | PDEKind::Burgers1D => {
                for index in 0..count {
                    if index % 2 == 0 {
                        let t = rng.gen::<f64>();
                        let x = if rng.gen_bool(0.5) { 0.0 } else { 1.0 };
                        points.extend([x, t]);
                        values.push(0.0);
                    } else {
                        let x = rng.gen::<f64>();
                        points.extend([x, 0.0]);
                        values.push(self.initial_condition(x));
                    }
                }
            }
        }

        (
            Array2::from_shape_vec((count, self.config.pde.kind.input_dim()), points).unwrap(),
            Array1::from_vec(values),
        )
    }

    fn backward_pde(&mut self, x_collocation: &Array2<f64>) -> f64 {
        let delta = (self.config.epsilon * 10.0).max(1e-4);
        let base_loss = self.compute_pde_residual(x_collocation);

        for layer_index in 0..self.network.get_layers().len() {
            let (rows, cols) = self.network.get_layers()[layer_index].weights.dim();
            for row in 0..rows {
                for col in 0..cols {
                    let original = self.network.get_layers()[layer_index].weights[[row, col]];
                    self.network.get_layers_mut()[layer_index].weights[[row, col]] = original + delta;
                    let loss_plus = self.compute_pde_residual(x_collocation);
                    self.network.get_layers_mut()[layer_index].weights[[row, col]] = original;
                    let grad = (loss_plus - base_loss) / delta;
                    self.network.get_layers_mut()[layer_index].weights_grad[[row, col]] += grad;
                }
            }

            let bias_len = self.network.get_layers()[layer_index].bias.len();
            for col in 0..bias_len {
                let original = self.network.get_layers()[layer_index].bias[col];
                self.network.get_layers_mut()[layer_index].bias[col] = original + delta;
                let loss_plus = self.compute_pde_residual(x_collocation);
                self.network.get_layers_mut()[layer_index].bias[col] = original;
                let grad = (loss_plus - base_loss) / delta;
                self.network.get_layers_mut()[layer_index].bias_grad[col] += grad;
            }
        }

        base_loss
    }

    pub fn train_epoch(
        &mut self,
        x_collocation: &Array2<f64>,
        x_boundary: &Array2<f64>,
        u_boundary: &Array1<f64>,
    ) -> f64 {
        self.network.zero_grads();

        let mut boundary_loss = 0.0;
        if x_boundary.nrows() > 0 {
            for index in 0..x_boundary.nrows() {
                let point = x_boundary.row(index).to_owned();
                let prediction = self.network.forward(&point)[0];
                let diff = prediction - u_boundary[index];
                boundary_loss += diff * diff;

                let grad_scale = 2.0 * self.config.lambda_boundary / x_boundary.nrows() as f64;
                let grad = Array1::from_vec(vec![diff * grad_scale]);
                self.network.backward(&grad);
            }

            boundary_loss /= x_boundary.nrows() as f64;
        }

        let pde_loss = self.backward_pde(x_collocation);
        self.optimizer.step(&mut self.network);

        pde_loss + self.config.lambda_boundary * boundary_loss
    }

    pub fn train(&mut self, x_data: &Array2<f64>, epochs: usize, n_boundary: usize) -> Vec<f64> {
        let collocation_points = self.prepare_collocation_points(x_data);
        let (x_boundary, u_boundary) = self.generate_boundary_conditions(n_boundary);
        let mut losses = Vec::with_capacity(epochs);

        for epoch in 0..epochs {
            let collocation_batch = self.sample_collocation_batch(&collocation_points);
            let loss = self.train_epoch(&collocation_batch, &x_boundary, &u_boundary);
            losses.push(loss);

            if epoch % 100 == 0 {
                println!("Epoch {}: Loss = {:.6}", epoch, loss);
            }
        }

        losses
    }

    pub fn predict(&self, x: &Array1<f64>) -> f64 {
        self.pde_output(x)
    }
}
