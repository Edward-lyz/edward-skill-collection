# Thread state

**Short:** Nsys's per-thread execution status over time, shown on the ``Thread State`` timeline row - a layered model that mixes kernel scheduler states, OS-runtime-library (OSRT) wait estimates, and sampling-inferred activity to indicate whether a thread is on a CPU, descheduled, or blocked. Not a pure OS state: Nsys synthesizes and estimates additional labels on top of what the kernel reports.

**Details:**

- Three sources feed the row: OS-reported states from context-switch tracing (Running, Blocked, Blocked (uninterruptible), Stopped, Terminated, Initialized, Transition); Nsys-synthesized states derived from sched events (Ready to run when the thread was preempted while running, Unscheduled when the OS state is unknown); and estimated states from OSRT interception or pure sampling (Waiting, In OS runtime library function, Likely running, Likely waiting). On x86_64 with CPU sampling, these collapse to just Running and Blocked.
- Wait reasons (Mutex, CondVar, UserRequest, Resource, KeyedEvent, PhysicalFault, NetSend/NetReply, TimerDelegate, Suspended, and so on) are not part of the state itself; they live on the separate ``Blocked State`` row, sourced from ``threadBlock`` on sched-out events in ``SCHED_EVENTS``. They are meaningful only when the (block reason, thread state) pair indicates blocking - ``NonBlocked`` paired with ``Running`` is ordinary preemption, not contention.
- On the timeline, the non-Running segments on the Thread State row are the gaps between useful work; hover the corresponding interval on Blocked State to see why the thread was off-CPU.
- When thread-activity collection includes backtraces, a single stack captured at the wake (sched-in) point, or at a long OSRT call, is attached to the blocked region - Nsys does not separately capture a waker-thread stack.
- Long Ready to run segments point to oversubscription or priority preemption (a higher-priority thread, DPC, or interrupt taking the core), not to the thread's own code.

**See also:**

- [CPU sampling](cpu-sampling.md)
- [CPU bound](../graphics-glossary/cpu-bound.md)
