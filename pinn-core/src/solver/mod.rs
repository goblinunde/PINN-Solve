// PDE求解器模块
use ndarray::{Array1, Array2};
use crate::nn::Network;

pub struct PDESolver {
    network: Network,
    learning_rate: f64,
}

impl PDESolver {
    pub fn new(layer_sizes: Vec<usize>, learning_rate: f64) -> Self {
        Self {
            network: Network::new(layer_sizes),
            learning_rate,
        }
    }

    pub fn train(&mut self, x_data: &Array2<f64>, epochs: usize) -> Vec<f64> {
        let mut losses = Vec::new();
        
        for epoch in 0..epochs {
            let mut total_loss = 0.0;
            
            for i in 0..x_data.nrows() {
                let input = x_data.row(i).to_owned();
                let output = self.network.forward(&input);
                let loss = output[0].powi(2); // 简化的损失函数
                total_loss += loss;
            }
            
            let avg_loss = total_loss / x_data.nrows() as f64;
            losses.push(avg_loss);
            
            if epoch % 1000 == 0 {
                println!("Epoch {}: Loss = {:.6}", epoch, avg_loss);
            }
        }
        
        losses
    }

    pub fn predict(&self, x: &Array1<f64>) -> f64 {
        self.network.forward(x)[0]
    }
}
