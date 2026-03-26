pub mod autodiff;
pub mod nn;
pub mod solver;
pub mod numerics;
pub mod gpu;
pub mod bindings;

use pyo3::prelude::*;

#[pymodule]
fn pinn_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<bindings::Network>()?;
    m.add_class::<bindings::Solver>()?;
    Ok(())
}
