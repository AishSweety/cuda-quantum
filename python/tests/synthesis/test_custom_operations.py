# ============================================================================ #
# Copyright (c) 2022 - 2024 NVIDIA Corporation & Affiliates.                   #
# All rights reserved.                                                         #
#                                                                              #
# This source code and the accompanying materials are made available under     #
# the terms of the Apache License 2.0 which accompanies this distribution.     #
# ============================================================================ #

import pytest
import numpy as np
import cudaq


@pytest.fixture(autouse=True)
def do_something():
    cudaq.reset_target()
    yield
    cudaq.__clearKernelRegistries()


def check_bell(entity):
    """Helper function to encapsulate checks for Bell pair"""
    counts = cudaq.sample(entity, shots_count=100)
    counts.dump()
    assert len(counts) == 2
    assert '00' in counts and '11' in counts


def test_basic():
    """
    Showcase user-level APIs of how to 
    (a) define a custom operation using unitary, 
    (b) how to use it in kernel, 
    (c) express controlled custom operation
    """

    cudaq.register_operation("custom_h",
                             1. / np.sqrt(2.) * np.array([1, 1, 1, -1]))
    cudaq.register_operation("custom_x", np.array([0, 1, 1, 0]))

    @cudaq.kernel
    def bell():
        qubits = cudaq.qvector(2)
        custom_h(qubits[0])
        custom_x.ctrl(qubits[0], qubits[1])

    check_bell(bell)


def test_cnot_gate():
    """Test CNOT gate"""

    cudaq.register_operation(
        "custom_cnot",
        np.array([1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0]))

    @cudaq.kernel
    def bell_pair():
        qubits = cudaq.qvector(2)
        h(qubits[0])
        custom_cnot(qubits[0], qubits[1])

    check_bell(bell_pair)


def test_cz_gate():
    """Test 2-qubit custom operation replicating CZ gate."""

    cudaq.register_operation(
        "custom_cz", np.array([1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0,
                               -1]))

    @cudaq.kernel
    def ctrl_z_kernel():
        qubits = cudaq.qvector(5)
        controls = cudaq.qvector(2)
        custom_cz(qubits[1], qubits[0])
        x(qubits[2])
        custom_cz(qubits[3], qubits[2])
        x(controls)

    counts = cudaq.sample(ctrl_z_kernel)
    assert counts["0010011"] == 1000


def test_three_qubit_op():
    """Test three-qubit operation replicating Toffoli gate."""

    cudaq.register_operation(
        "toffoli",
        np.array([
            1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0,
            0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0
        ]))

    @cudaq.kernel
    def test_toffoli():
        q = cudaq.qvector(3)
        x(q)
        toffoli(q[0], q[1], q[2])

    counts = cudaq.sample(test_toffoli)
    print(counts)
    assert counts["110"] == 1000


# NOTE / [SKIP_TEST]: The following test crashes in the 'Validate Python wheel (amd64 / x86)'
# stage on Ubuntu, RedHat and OpenSuse for 'tensornet' and 'tensornet-mps' backends
# (works on Debian and Fedora, and on all for arm64 in CI, and locally).
@pytest.mark.parametrize("target", [
    'density-matrix-cpu', 'nvidia', 'nvidia-fp64', 'nvidia-mqpu',
    'nvidia-mqpu-fp64', 'qpp-cpu'
])
def test_simulators(target):
    """Test simulation of custom operation on all available simulation targets."""

    def can_set_target(name):
        target_installed = True
        try:
            cudaq.set_target(name)
        except RuntimeError:
            target_installed = False
        return target_installed

    if can_set_target(target):
        test_basic()
        test_cnot_gate()
        test_three_qubit_op()
        cudaq.reset_target()
    else:
        pytest.skip("target not available")

    cudaq.reset_target()


def test_custom_adjoint():
    """Test that adjoint can be called on custom operations."""

    cudaq.register_operation("custom_s", np.array([1, 0, 0, 1j]))

    cudaq.register_operation("custom_s_adj", np.array([1, 0, 0, -1j]))

    @cudaq.kernel
    def kernel():
        q = cudaq.qubit()
        h(q)
        custom_s.adj(q)
        custom_s_adj(q)
        h(q)

    counts = cudaq.sample(kernel)
    counts.dump()
    assert counts["1"] == 1000


def test_incorrect_matrix():
    """Incorrectly sized matrix raises error."""

    with pytest.raises(AssertionError) as error:
        cudaq.register_operation("invalid_op",
                                 np.array([1, 0, 0, 0, 1, 0, 0, 0, 1]))


def test_bad_attribute():
    """Test that unsupported attributes on custom operations raise error."""

    cudaq.register_operation("custom_s", np.array([1, 0, 0, 1j]))

    @cudaq.kernel
    def kernel():
        q = cudaq.qubit()
        custom_s.foo(q)
        mz(q)

    with pytest.raises(Exception) as error:
        cudaq.sample(kernel)


def test_builder_mode():
    """Builder-mode API """

    kernel = cudaq.make_kernel()
    cudaq.register_operation("custom_h",
                             1. / np.sqrt(2.) * np.array([1, 1, 1, -1]))

    qubits = kernel.qalloc(2)
    kernel.custom_h(qubits[0])
    kernel.cx(qubits[0], qubits[1])

    check_bell(kernel)


# leave for gdb debugging
if __name__ == "__main__":
    loc = os.path.abspath(__file__)
    pytest.main([loc, "-rP"])
