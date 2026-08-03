---
source_path: UserGuide/topics/ucx-library-trace.rst
title: ## UCX API Trace
---
## UCX API Trace

If UCX API trace is selected Nsight Systems will trace the subset of functions
of the UCX protocol layer UCP that are most likely be involved in performance
bottlenecks. To keep overhead low Nsight Systems does not trace all functions.

The following environment variables control what is recorded:

-  ``NSYS_UCP_COMM_SUBMIT``: (enabled by default) If set to ``0``, UCP communication
   submission calls are not recorded any more. These calls are usually short,
   because the communication itself is handled in a worker thread.
-  ``NSYS_UCP_COMM_PROGRESS``: (enabled by default) If set to ``0``, tracking of
   (process-local) UCP communication progress is disabled. The progress tracking
   uses UCP completion callbacks.
-  ``NSYS_UCP_COMM_PARAMS``: (enabled by default) If set to ``0``, UCP communication
   parameters (tag, remote worker UID, packed message size, buffer address) will
   not be recorded. Recording the remote worker UID requires UCX >= 1.12.0.
   Recording the packed message size requires UCX >= 1.14.0.


#### UCX functions traced

::

   ucp_am_send_nb[x]
   ucp_am_recv_data_nbx
   ucp_am_data_release
   ucp_atomic_{add{32,64},cswap{32,64},fadd{32,64},swap{32,64}}
   ucp_atomic_{post,fetch_nb,op_nbx}
   ucp_cleanup
   ucp_config_{modify,read,release}
   ucp_disconnect_nb
   ucp_dt_{create_generic,destroy}
   ucp_ep_{create,destroy,modify_nb,close_nbx}
   ucp_ep_flush[{_nb,_nbx}]
   ucp_listener_{create,destroy,query,reject}
   ucp_mem_{advise,map,unmap,query}
   ucp_{put,get}[_nbi]
   ucp_{put,get}_nb[x]
   ucp_request_{alloc,cancel,is_completed}
   ucp_rkey_{buffer_release,destroy,pack,ptr}
   ucp_stream_data_release
   ucp_stream_recv_data_nb
   ucp_stream_{send,recv}_nb[x]
   ucp_stream_worker_poll
   ucp_tag_msg_recv_nb[x]
   ucp_tag_{send,recv}_nbr
   ucp_tag_{send,recv}_nb[x]
   ucp_tag_send_sync_nb[x]
   ucp_worker_{create,destroy,get_address,get_efd,arm,fence,wait,signal,wait_mem}
   ucp_worker_flush[{_nb,_nbx}]
   ucp_worker_set_am_{handler,recv_handler}
         

**UCX Functions Not Traced:**

::

   ucp_config_print
   ucp_conn_request_query
   ucp_context_{query,print_info}
   ucp_get_version[_string]
   ucp_ep_{close_nb,print_info,query,rkey_unpack}
   ucp_mem_print_info
   ucp_request_{check_status,free,query,release,test}
   ucp_stream_recv_request_test
   ucp_tag_probe_nb
   ucp_tag_recv_request_test
   ucp_worker_{address_query,print_info,progress,query,release_address}
          

Additional API functions from other UCX layers may be added in a future version of the product.
