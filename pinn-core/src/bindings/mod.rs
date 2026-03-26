// Python绑定
use pyo3::prelude::*;
use ndarray::{Array1, Array2};
use crate::solver::PDESolver as RustSolver;

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

#[pymethods]
impl Solver {
    #[new]
    fn new(layers: Vec<usize>, learning_rate: f64) -> Self {
        Self {
            solver: RustSolver::new(layers, learning_rate),
        }
    }

    fn train(&mut self, x_data: Vec<Vec<f64>>, epochs: usize, n_boundary: usize) -> Vec<f64> {
        let rows = x_data.len();
        let cols = x_data[0].len();
        let flat: Vec<f64> = x_data.into_iter().flatten().collect();
        let array = Array2::from_shape_vec((rows, cols), flat).unwrap();
        
        self.solver.train(&array, epochs, n_boundary)
    }

    fn predict(&mut self, x: Vec<f64>) -> f64 {
        let input = Array1::from_vec(x);
        self.solver.predict(&input)
    }
    
    fn predict_batch(&mut self, x_data: Vec<Vec<f64>>) -> Vec<f64> {
        x_data.into_iter().map(|x| {
            let input = Array1::from_vec(x);
            self.solver.predict(&input)
        }).collect()
    }
}
