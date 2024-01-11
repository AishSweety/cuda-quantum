Taking Advantage of the Underlying Quantum Platform
---------------------------------------------------
The CUDA Quantum machine model elucidates the various devices considered in the 
broader quantum-classical compute node context. Programmers will have one or many 
host CPUs, zero or many NVIDIA GPUs, a classical QPU control space, and the
quantum register itself. Moreover, the :doc:`specification </specification/cudaq/platform>`
notes that the underlying platform may expose multiple QPUs. In the near-term,
this will be unlikely with physical QPU instantiations, but the availability of
GPU-based circuit simulators on NVIDIA multi-GPU architectures does give one an
opportunity to think about programming such a multi-QPU architecture in the near-term.
CUDA Quantum starts by enabling one to query information about the underlying quantum
platform via the :code:`quantum_platform` abstraction. This type exposes a
:code:`num_qpus()` method that can be used to query the number of available
QPUs for asynchronous CUDA Quantum kernel and :code:`cudaq::` function invocations.
Each available QPU is assigned a logical index, and programmers can launch
specific asynchronous function invocations targeting a desired QPU.


NVIDIA `MQPU` Platform
++++++++++++++++++++++

The NVIDIA `MQPU` target (:code:`nvidia-mqpu`) provides a simulated QPU for every available NVIDIA GPU on the underlying system. 
Each QPU is simulated via a `cuStateVec` simulator backend. 
This target enables asynchronous parallel execution of quantum kernel tasks.

Here is a simple example demonstrating its usage.

.. tab:: C++

    .. literalinclude:: ../../snippets/cpp/using/cudaq/platform/sample_async.cpp
        :language: cpp
        :start-after: [Begin Documentation]
        :end-before: [End Documentation]

    CUDA Quantum exposes asynchronous versions of the default :code:`cudaq::` algorithmic
    primitive functions like :code:`sample` and :code:`observe` (e.g., :code:`cudaq::sample_async` function in the above code snippet).

    One can specify the target multi-QPU architecture (:code:`nvidia-mqpu`) with the :code:`--target` flag:
    
    .. code-block:: console

        nvq++ sample_async.cpp -target nvidia-mqpu
        ./a.out

.. tab:: Python

    .. literalinclude:: ../../snippets/python/using/cudaq/platform/sample_async.py
        :language: python
        :start-after: [Begin Documentation]

Depending on the number of GPUs available on the system, the :code:`nvidia-mqpu` platform will create the same number of virtual QPU instances.
For example, on a system with 4 GPUs, the above code will distribute the four sampling tasks among those :code:`GPUEmulatedQPU` instances.

The results might look like the following 4 different random samplings:

.. code-block:: console
  
    Number of QPUs: 4
    { 10011:28 01100:28 ... }
    { 10011:37 01100:25 ... }
    { 10011:29 01100:25 ... }
    { 10011:33 01100:30 ... }

.. note::

  By default, the :code:`nvidia-mqpu` platform will utilize all available GPUs (number of QPUs instances is equal to the number of GPUs).
  To specify the number QPUs to be instantiated, one can set the :code:`CUDAQ_MQPU_NGPUS` environment variable.
  For example, use :code:`export CUDAQ_MQPU_NGPUS=2` to specify that only 2 QPUs (GPUs) are needed.

Asynchronous expectation value computations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

One typical use case of the :code:`nvidia-mqpu` platform is to distribute the
expectation value computations of a multi-term Hamiltonian across multiple virtual QPUs (:code:`GPUEmulatedQPU`).

Here is an example.

.. tab:: C++

    .. literalinclude:: ../../snippets/cpp/using/cudaq/platform/observe_mqpu.cpp
        :language: cpp
        :start-after: [Begin Documentation]
        :end-before: [End Documentation]


    One can then target the :code:`nvidia-mqpu` platform by executing the following commands:

    .. code-block:: console

        nvq++ observe_mqpu.cpp -target nvidia-mqpu
        ./a.out

.. tab:: Python

    .. literalinclude:: ../../snippets/python/using/cudaq/platform/observe_mqpu.py
        :language: python
        :start-after: [Begin Documentation]

In the above code snippets, since the Hamiltonian contains four non-identity terms, there are four quantum circuits that need to be executed
in order to compute the expectation value of that Hamiltonian and given the quantum state prepared by the ansatz kernel. When the :code:`nvidia-mqpu` platform
is selected, these circuits will be distributed across all available QPUs. The final expectation value result is computed from all QPU execution results.

Parallel distribution mode
^^^^^^^^^^^^^^^^^^^^^^^^^^

The CUDA Quantum :code:`nvidia-mqpu` platform supports two modes of parallel distribution of expectation value computation:

* MPI: distribute the expectation value computations across available MPI ranks and GPUs for each Hamiltonian term.
* Thread: distribute the expectation value computations among available GPUs via standard C++ threads (each thread handles one GPU).

For instance, if all GPUs are available on a single node, thread-based parallel distribution 
(:code:`cudaq::parallel::thread` in C++ or :code:`cudaq.parallel.thread` in Python, as shown in the above example) is sufficient.
On the other hand, if one wants to distribute the tasks across GPUs on multiple nodes, e.g., on a compute cluster, MPI distribution mode
should be used.

An example of MPI distribution mode usage in both C++ and Python is given below:

.. tab:: C++

    .. literalinclude:: ../../snippets/cpp/using/cudaq/platform/observe_mqpu_mpi.cpp
        :language: cpp
        :start-after: [Begin Documentation]
        :end-before: [End Documentation]

    .. code-block:: console

        nvq++ file.cpp -target nvidia-mqpu
        mpirun -np <N> a.out


.. tab:: Python

    .. literalinclude:: ../../snippets/python/using/cudaq/platform/observe_mqpu_mpi.py
        :language: python
        :start-after: [Begin Documentation]

    .. code-block:: console

        mpirun -np <N> python3 file.py

In the above example, the parallel distribution mode was set to :code:`mpi` using :code:`cudaq::parallel::mpi` in C++ or :code:`cudaq.parallel.mpi` in Python.
CUDA Quantum provides MPI utility functions to initialize, finalize, or query (rank, size, etc.) the MPI runtime. 
Last but not least, the compiled executable (C++) or Python script needs to be launched with an appropriate MPI command, 
e.g., :code:`mpirun`, :code:`mpiexec`, :code:`srun`, etc.

Remote REST Server Platform
+++++++++++++++++++++++++++

The remote simulator target (:code:`remote-sim`) encapsulates simulated QPUs
as independent REST server instances. The CUDA Quantum runtime communicates via HTTP requests (REST API) to these REST server instances. 

Please refer to the `Open API Docs <../../openapi.html>`_  for the latest API information.

CUDA Quantum provides the REST server implementation as a standalone application (:code:`cudaq-qpud`),
hosting all the simulator backends available in the installation. These backends include those that require MPI for multi-GPU computation.

Auto-launch REST Server
^^^^^^^^^^^^^^^^^^^^^^^

The server app (:code:`cudaq-qpud`) can be launch and shutdown automatically
by using the auto-launch feature of the platform.
Random TCP/IP ports, that are available for use, will be selected to launch those server processes.

.. tab:: C++

    .. code-block:: console

        nvq++ file.cpp --target remote-sim --remote-sim-auto-launch <N> --remote-sim-backend <sim1[,sim2,...]>


.. tab:: Python

     .. code:: python 

        cudaq.set_target("remote-sim", auto_launch="<N>", backend="sim1[,sim2,...]")


In the above snippets, `N` denotes the number of REST server instances (QPUs) to be launched.
These servers will be shut down at the end of the execution.

Manually Launch REST Server
^^^^^^^^^^^^^^^^^^^^^^^^^^^

To start the server, serving at a specific TCP/IP port, one can do the following.

.. code-block:: console
    
    cudaq-qpud --port <port number>

User code can then target this platform by specifying its target name (:code:`remote-sim`).

.. tab:: C++

    .. code-block:: console

        nvq++ file.cpp --target remote-sim --remote-sim-url <url1[,url2,...]> --remote-sim-backend <sim1[,sim2,...]>


.. tab:: Python

     .. code:: python 

        cudaq.set_target("remote-sim", url="url1[,url2,...]", backend="sim1[,sim2,...]")
    

When using this target, the user needs to provides a list of URLs where (:code:`cudaq-qpud`) is serving.
The number of QPUs (:code:`num_qpus()`) is equal to the number of URLs provided. 

Each QPU instance can be assigned a different backend simulator via the :code:`--remote-sim-backend` (`nvq++`) or :code:`backend` (Python)
option. Otherwise, if a single backend is specified, all the QPUs are assumed to be using the same simulator.

Supported Kernel Arguments
^^^^^^^^^^^^^^^^^^^^^^^^^^

To invoke quantum kernels on the remote server, the (:code:`remote-sim`) platform will serialize
runtime arguments into a flat memory buffer (`args` field of the request JSON).

Currently, the following data types are supported.

.. list-table:: 
   :widths: 50 50 50
   :header-rows: 1

   * - Data type
     - Example
     - Serialization
   * -  Trivial type (occupies a contiguous memory area)
     -  `int`, `std::size_t`, `double`, etc.
     - Byte data (via `memcopy`)
   * - `std::vector` of trivial type
     - `std::vector<int>`, `std::vector<double>`, etc. 
     - Total vector size in bytes as a 64-bit integer followed by serialized data of all vector elements.
  