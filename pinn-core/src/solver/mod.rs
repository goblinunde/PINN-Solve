// PDE求解器模块
use ndarray::{Array1, Array2};
use crate::nn::{Network, AdamOptimizer};
use crate::autodiff::{compute_derivative, compute_second_derivative};
use rand::Rng;

pub struct PDESolver {
    network: Network,
    optimizer: AdamOptimizer,
    epsilon: f64, // 数值微分步长
}

impl PDESolver {
    pub fn new(layer_sizes: Vec<usize>, learning_rate: f64) -> Self {
        let mut network = Network::new(layer_sizes);
        let optimizer = AdamOptimizer::new(&network, learning_rate);
        
        Self {
            network,
            optimizer,
            epsilon: 1e-5,
        }
    }

    /// 计算PDE残差（以2D Poisson方程为例: u_xx + u_yy = f）
    pub fn compute_pde_residual(&mut self, x: &Array2<f64>) -> f64 {
        let mut total_residual = 0.0;
        
        for i in 0..x.nrows() {
            let point = x.row(i).to_owned();
            
            // 计算 u(x,y)
            let u = self.network.forward(&point)[0];
            
            // 计算一阶偏导数
            let mut point_x_plus = point.clone();
            let mut point_x_minus = point.clone();
            point_x_plus[0] += self.epsilon;
            point_x_minus[0] -= self.epsilon;
            let u_x_plus = self.network.forward(&point_x_plus)[0];
            let u_x_minus = self.network.forward(&point_x_minus)[0];
            
            let mut point_y_plus = point.clone();
            let mut point_y_minus = point.clone();
            point_y_plus[1] += self.epsilon;
            point_y_minus[1] -= self.epsilon;
            let u_y_plus = self.network.forward(&point_y_plus)[0];
            let u_y_minus = self.network.forward(&point_y_minus)[0];
            
            // 计算二阶偏导数
            let u_xx = (u_x_plus - 2.0 * u + u_x_minus) / (self.epsilon * self.epsilon);
            let u_yy = (u_y_plus - 2.0 * u + u_y_minus) / (self.epsilon * self.epsilon);
            
            // PDE残差: u_xx + u_yy = 0 (Laplace方程)
            let residual = u_xx + u_yy;
            total_residual += residual * residual;
        }
        
        total_residual / x.nrows() as f64
    }

    /// 计算边界条件损失
    pub fn compute_boundary_loss(&mut self, x_boundary: &Array2<f64>, u_boundary: &Array1<f64>) -> f64 {
        let mut total_loss = 0.0;
        
        for i in 0..x_boundary.nrows() {
            let point = x_boundary.row(i).to_owned();
            let u_pred = self.network.forward(&point)[0];
            let diff = u_pred - u_boundary[i];
            total_loss += diff * diff;
        }
        
        total_loss / x_boundary.nrows() as f64
    }

    /// 训练一个epoch
    pub fn train_epoch(
        &mut self,
        x_collocation: &Array2<f64>,
        x_boundary: &Array2<f64>,
        u_boundary: &Array1<f64>,
        lambda_boundary: f64,
    ) -> f64 {
        // 计算总损失
        let pde_loss = self.compute_pde_residual(x_collocation);
        let boundary_loss = self.compute_boundary_loss(x_boundary, u_boundary);
        let total_loss = pde_loss + lambda_boundary * boundary_loss;
        
        // 反向传播（简化版：使用数值梯度）
        self.backward_numerical(x_collocation, x_boundary, u_boundary, lambda_boundary);
        
        // 优化器更新
        self.optimizer.step(&mut self.network);
        
        total_loss
    }

    /// 数值梯度反向传播
    fn backward_numerical(
        &mut self,
        x_collocation: &Array2<f64>,
        x_boundary: &Array2<f64>,
        u_boundary: &Array1<f64>,
        lambda_boundary: f64,
    ) {
        let delta = 1e-5;
        
        // 对每一层的权重和偏置计算梯度
        for layer_idx in 0..self.network.get_layers().len() {
            let (rows, cols) = self.network.get_layers()[layer_idx].weights.dim();
            
            // 权重梯度
            for i in 0..rows {
                for j in 0..cols {
                    // 保存原值
                    let original = self.network.get_layers_mut()[layer_idx].weights[[i, j]];
                    
                    // 计算 f(w + delta)
                    self.network.get_layers_mut()[layer_idx].weights[[i, j]] = original + delta;
                    let loss_plus = self.compute_pde_residual(x_collocation)
                        + lambda_boundary * self.compute_boundary_loss(x_boundary, u_boundary);
                    
                    // 计算 f(w - delta)
                    self.network.get_layers_mut()[layer_idx].weights[[i, j]] = original - delta;
                    let loss_minus = self.compute_pde_residual(x_collocation)
                        + lambda_boundary * self.compute_boundary_loss(x_boundary, u_boundary);
                    
                    // 恢复原值
                    self.network.get_layers_mut()[layer_idx].weights[[i, j]] = original;
                    
                    // 计算梯度
                    let grad = (loss_plus - loss_minus) / (2.0 * delta);
                    self.network.get_layers_mut()[layer_idx].weights_grad[[i, j]] = grad;
                }
            }
            
            // 偏置梯度
            for j in 0..self.network.get_layers()[layer_idx].bias.len() {
                let original = self.network.get_layers_mut()[layer_idx].bias[j];
                
                self.network.get_layers_mut()[layer_idx].bias[j] = original + delta;
                let loss_plus = self.compute_pde_residual(x_collocation)
                    + lambda_boundary * self.compute_boundary_loss(x_boundary, u_boundary);
                
                self.network.get_layers_mut()[layer_idx].bias[j] = original - delta;
                let loss_minus = self.compute_pde_residual(x_collocation)
                    + lambda_boundary * self.compute_boundary_loss(x_boundary, u_boundary);
                
                self.network.get_layers_mut()[layer_idx].bias[j] = original;
                
                let grad = (loss_plus - loss_minus) / (2.0 * delta);
                self.network.get_layers_mut()[layer_idx].bias_grad[j] = grad;
            }
        }
    }

    /// 完整训练流程
    pub fn train(
        &mut self,
        x_data: &Array2<f64>,
        epochs: usize,
        n_boundary: usize,
    ) -> Vec<f64> {
        let mut losses = Vec::new();
        let mut rng = rand::thread_rng();
        
        // 生成边界点（简化：使用域的边界）
        let mut x_boundary = Vec::new();
        let mut u_boundary = Vec::new();
        
        for _ in 0..n_boundary {
            let side = rng.gen_range(0..4);
            let t = rng.gen::<f64>();
            
            let (x, y) = match side {
                0 => (0.0, t),      // 左边界
                1 => (1.0, t),      // 右边界
                2 => (t, 0.0),      // 下边界
                _ => (t, 1.0),      // 上边界
            };
            
            x_boundary.push(vec![x, y]);
            u_boundary.push(0.0); // Dirichlet边界条件: u = 0
        }
        
        let x_boundary = Array2::from_shape_vec(
            (n_boundary, 2),
            x_boundary.into_iter().flatten().collect(),
        ).unwrap();
        let u_boundary = Array1::from_vec(u_boundary);
        
        // 训练循环
        for epoch in 0..epochs {
            let loss = self.train_epoch(x_data, &x_boundary, &u_boundary, 10.0);
            losses.push(loss);
            
            if epoch % 100 == 0 {
                println!("Epoch {}: Loss = {:.6}", epoch, loss);
            }
        }
        
        losses
    }

    pub fn predict(&mut self, x: &Array1<f64>) -> f64 {
        self.network.forward(x)[0]
    }
}
