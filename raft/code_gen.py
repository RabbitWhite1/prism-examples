buf_size = 2
num_nodes = 2

prologue_code = """
// raft election algorithm

dtmc

const int MAX_TIME = 64;
const int MAX_TERM = 3;
const int ELECTION_TIMEOUT = 20;
const int delay = 2;
const int ttl = 5;

const int TYPE_RV = 0;
const int TYPE_RVR = 1;

const int FOLLOWER=0;
const int CANDIDATE=1;
const int LEADER=2;

module global_time
    global_time: [0..MAX_TIME+1] init 0;
    [time] global_time<MAX_TIME -> (global_time'=global_time+1);
    [time] global_time=MAX_TIME -> (global_time'=global_time);
endmodule
"""

# 1. `n` slot for packets
# 2. Each slot has a `valid` marker
# 3. When sending a packet, the first slot with `valid==false` is used
# 4. When receiving a packet, non-deterministically choose a slot with `valid==true`
# 5. After `delay` time, the packet is removed
wire_code = """
module wire12
""" + ''.join([f"""
    pkt_valid_12_{i} : bool init false;
    pkt_type_12_{i} : [0..1] init 0; // 0: RV; 1: RVR
    pkt_term_12_{i} : [0..MAX_TERM+1] init 0;
    pkt_success_12_{i} : bool init false;
    time_12_{i} : [0..ttl+1] init 0;
""" for i in range(buf_size)]) + """
    // send packet """ + ''.join([f"""
    [election_timeout_1] election_time_1=ELECTION_TIMEOUT & pkt_valid_12_{i}=false & term_1<MAX_TERM -> (pkt_valid_12_{i}'=true) & (pkt_type_12_{i}'=TYPE_RV) & (pkt_term_12_{i}'=term_1+1) & (time_12_{i}'=0);
    [election_timeout_1] election_time_1=ELECTION_TIMEOUT & pkt_valid_12_{i}=false & term_1=MAX_TERM -> true;
    [time]         pkt_valid_12_{i}=false -> (time_12_{i}'=0);
    [time]         pkt_valid_12_{i}=true & time_12_{i}<ttl -> (time_12_{i}'=time_12_{i}+1);
    [time]         pkt_valid_12_{i}=true & time_12_{i}=ttl -> (pkt_valid_12_{i}'=false) & (pkt_term_12_{i}'=0) & (time_12_{i}'=0);
""" for i in range(buf_size)]) + """
    // recv packet """ + ''.join([f"""
    [recv_rv_12_{i}] pkt_valid_12_{i}=true & pkt_type_12_{i}=TYPE_RV & time_12_{i} >= delay -> (pkt_valid_12_{i}'=false);
    // TODO: should choose a empty slot to use (currently directly use the same slot)
    [recv_rv_21_{i}] pkt_valid_21_{i}=true & pkt_type_21_{i}=TYPE_RV & pkt_term_21_{i}<=term_1 & time_21_{i} >= delay -> (pkt_valid_12_{i}'=true) & (pkt_type_12_{i}'=TYPE_RVR) & (pkt_term_12_{i}'=0) & (pkt_success_12_{i}'=false) & (time_12_{i}'=0);
    [recv_rv_21_{i}] pkt_valid_21_{i}=true & pkt_type_21_{i}=TYPE_RV & pkt_term_21_{i}>term_1 & time_21_{i} >= delay -> (pkt_valid_12_{i}'=true) & (pkt_type_12_{i}'=TYPE_RVR) & (pkt_term_12_{i}'=0) & (pkt_success_12_{i}'=true) & (time_12_{i}'=0);
    [recv_rvr_12_{i}] pkt_valid_12_{i}=true & pkt_type_12_{i}=TYPE_RVR & time_12_{i} >= delay -> (pkt_valid_12_{i}'=false) & (pkt_type_12_{i}'=0) & (pkt_term_12_{i}'=0) & (pkt_success_12_{i}'=false) & (time_12_{i}'=0);
""" for i in range(buf_size)]) + """
endmodule
"""

node_code = """
module node1
    role_1 : [0..3] init FOLLOWER;
    term_1 : [0..MAX_TERM+1] init 0;
    election_time_1 : [0..ELECTION_TIMEOUT+1] init 0;
""" + ''.join([f"""
    voted_1_{i} : bool init false;""" for i in range(num_nodes)]) + f"""

    [time] election_time_1<ELECTION_TIMEOUT -> (election_time_1'=election_time_1+1);
    [time] election_time_1=ELECTION_TIMEOUT -> (election_time_1'=election_time_1);
    [election_timeout_1] role_1!=LEADER & election_time_1=ELECTION_TIMEOUT & term_1<MAX_TERM -> (role_1'=CANDIDATE) & (term_1'=term_1+1) & (election_time_1'=0) & {' & '.join([f"(voted_1_{i}'=false)" for i in range(num_nodes)])};
    [election_timeout_terminate_1] election_time_1=ELECTION_TIMEOUT & term_1=MAX_TERM -> (term_1'=term_1) & (election_time_1'=0);
""" + ''.join([f"""
    [recv_rv_21_{i}] pkt_term_21_{i}>term_1 -> (term_1'=max(term_1, pkt_term_21_{i})) & (role_1'=FOLLOWER) & (election_time_1'=0);
    [recv_rv_21_{i}] pkt_term_21_{i}<=term_1 -> true;
    // hack elected leader
    [recv_rvr_21_{i}] role_1=CANDIDATE & pkt_success_21_{i}=true -> (voted_1_1'=true) & (role_1'=LEADER);
    [recv_rvr_21_{i}] role_1=CANDIDATE & pkt_success_21_{i}=false -> true;
""" for i in range(buf_size)]) + """
endmodule
"""

module_rename_codes = [
"""
module wire21=wire12[""" + ''.join([f"""
    pkt_valid_12_{i}=pkt_valid_21_{i}, pkt_type_12_{i}=pkt_type_21_{i}, pkt_term_12_{i}=pkt_term_21_{i}, pkt_success_12_{i}=pkt_success_21_{i}, time_12_{i}=time_21_{i},""" for i in range(buf_size)]) + ''.join([f"""
    pkt_valid_21_{i}=pkt_valid_12_{i}, pkt_type_21_{i}=pkt_type_12_{i}, pkt_term_21_{i}=pkt_term_12_{i}, pkt_success_21_{i}=pkt_success_12_{i}, time_21_{i}=time_12_{i},""" for i in range(buf_size)]) + """
    term_1=term_2, term_2=term_1, election_timeout_1=election_timeout_2, """ + ','.join([f"""
    recv_rv_12_{i}=recv_rv_21_{i}, recv_rv_21_{i}=recv_rv_12_{i}, recv_rvr_12_{i}=recv_rvr_21_{i}""" for i in range(buf_size)]) + """
] endmodule
""",
"""
module node2=node1[
    role_1=role_2, term_1=term_2, """ + ''.join([f"""
    voted_1_{i}=voted_2_{(i+1)%num_nodes}, """ for i in range(num_nodes)]) + ''.join([f"""
    pkt_term_21_{i}=pkt_term_12_{i}, recv_rv_21_{i}=recv_rv_12_{i}, recv_rvr_21_{i}=recv_rvr_12_{i}, """ for i in range(buf_size)]) + """
    election_time_1=election_time_2, election_timeout_1=election_timeout_2, election_timeout_terminate_1=election_timeout_terminate_2
] endmodule
""",
]

epilogue_code = """
// rewards (to calculate expected number of steps)
rewards "steps"
    true : 1;
endrewards

label "recv_rv_12_0_cond1" = role_1!=LEADER;
label "recv_rv_12_0_cond2" = election_time_1=ELECTION_TIMEOUT;
label "recv_rv_12_0_cond3" = term_1<MAX_TERM;

label "elected_1" = role_1=LEADER;
label "elected_2" = role_2=LEADER;
"""

code = ''.join([prologue_code, wire_code, node_code, ''.join(module_rename_codes), epilogue_code])
# print(code)
open('raft.pm', 'w').write(code)