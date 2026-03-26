// 神经网络模块
use ndarray::{Array1, Array2};
use rand::Rng;

pub struct Layer {
    pub weights: Array2<f64>,
    pub bias: Array1<f64>,
}

impl Layer {
    pub fn new(input_size: usize, output_size: usize) -> Self {
        let mut rng = rand::thread_rng();
        let scale = (2.0 / input_size as f64).sqrt();
        
        let weights = Array2::from_shape_fn((input_size, output_size), |_| {
            rng.gen::<f64>() * scale - scale / 2.0
        });
        let bias = Array1::zeros(output_size);
        
        Self { weights, bias }
    }

    pub fn forward(&self, input: &Array1<f64>) -> Array1<f64> {
        input.dot(&self.weights) + &self.bias
    }
}

pub enum Activation {
    Tanh,
    Sigmoid,
    ReLU,
}

impl Activation {
    pub fn apply(&self, x: &Array1<f64>) -> Array1<f64> {
        match self {
            Activation::Tanh => x.mapv(|v| v.tanh()),
            Activation::Sigmoid => x.mapv(|v| 1.0 / (1.0 + (-v).exp())),
            Activation::ReLU => x.mapv(|v| v.max(0.0)),
        }
    }
}

pub struct Network {
    layers: Vec<Layer>,
    activation: Activation,
}

impl Network {
    pub fn new(layer_sizes: Vec<usize>) -> Self {
        let mut layers = Vec::new();
        for i in 0..layer_sizes.len() - 1 {
            layers.push(Layer::new(layer_sizes[i], layer_sizes[i + 1]));
        }
        Self {
            layers,
            activation: Activation::Tanh,
        }
    }

    pub fn forward(&self, input: &Array1<f64>) -> Array1<f64> {
        let mut output = input.clone();
        for (i, layer) in self.layers.iter().enumerate() {
            output = layer.forward(&output);
            if i < self.layers.len() - 1 {
                output = self.activation.apply(&output);
            }
        }
        output
    }
}
