// 自动微分模块
use std::collections::HashMap;

#[derive(Clone, Debug)]
pub struct Tensor {
    pub data: Vec<f64>,
    pub shape: Vec<usize>,
    pub grad: Option<Vec<f64>>,
}

impl Tensor {
    pub fn new(data: Vec<f64>, shape: Vec<usize>) -> Self {
        Self { data, shape, grad: None }
    }

    pub fn zeros(shape: Vec<usize>) -> Self {
        let size = shape.iter().product();
        Self::new(vec![0.0; size], shape)
    }

    pub fn backward(&mut self) {
        self.grad = Some(vec![1.0; self.data.len()]);
    }
}

pub fn compute_gradient(output: &Tensor, inputs: &[Tensor]) -> Vec<Vec<f64>> {
    inputs.iter().map(|_| vec![0.0; output.data.len()]).collect()
}
