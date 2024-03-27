
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

module wire12

    pkt_valid_12_0 : bool init false;
    pkt_type_12_0 : [0..1] init 0; // 0: RV; 1: RVR
    pkt_term_12_0 : [0..MAX_TERM+1] init 0;
    pkt_success_12_0 : bool init false;
    time_12_0 : [0..ttl+1] init 0;

    pkt_valid_12_1 : bool init false;
    pkt_type_12_1 : [0..1] init 0; // 0: RV; 1: RVR
    pkt_term_12_1 : [0..MAX_TERM+1] init 0;
    pkt_success_12_1 : bool init false;
    time_12_1 : [0..ttl+1] init 0;

    // send packet 
    [election_timeout_1] election_time_1=ELECTION_TIMEOUT & pkt_valid_12_0=false & term_1<MAX_TERM -> (pkt_valid_12_0'=true) & (pkt_type_12_0'=TYPE_RV) & (pkt_term_12_0'=term_1+1) & (time_12_0'=0);
    [election_timeout_1] election_time_1=ELECTION_TIMEOUT & pkt_valid_12_0=false & term_1=MAX_TERM -> true;
    [time]         pkt_valid_12_0=false -> (time_12_0'=0);
    [time]         pkt_valid_12_0=true & time_12_0<ttl -> (time_12_0'=time_12_0+1);
    [time]         pkt_valid_12_0=true & time_12_0=ttl -> (pkt_valid_12_0'=false) & (pkt_term_12_0'=0) & (time_12_0'=0);

    [election_timeout_1] election_time_1=ELECTION_TIMEOUT & pkt_valid_12_1=false & term_1<MAX_TERM -> (pkt_valid_12_1'=true) & (pkt_type_12_1'=TYPE_RV) & (pkt_term_12_1'=term_1+1) & (time_12_1'=0);
    [election_timeout_1] election_time_1=ELECTION_TIMEOUT & pkt_valid_12_1=false & term_1=MAX_TERM -> true;
    [time]         pkt_valid_12_1=false -> (time_12_1'=0);
    [time]         pkt_valid_12_1=true & time_12_1<ttl -> (time_12_1'=time_12_1+1);
    [time]         pkt_valid_12_1=true & time_12_1=ttl -> (pkt_valid_12_1'=false) & (pkt_term_12_1'=0) & (time_12_1'=0);

    // recv packet 
    [recv_rv_12_0] pkt_valid_12_0=true & pkt_type_12_0=TYPE_RV & time_12_0 >= delay -> (pkt_valid_12_0'=false);
    // TODO: should choose a empty slot to use (currently directly use the same slot)
    [recv_rv_21_0] pkt_valid_21_0=true & pkt_type_21_0=TYPE_RV & pkt_term_21_0<=term_1 & time_21_0 >= delay -> (pkt_valid_12_0'=true) & (pkt_type_12_0'=TYPE_RVR) & (pkt_term_12_0'=0) & (pkt_success_12_0'=false) & (time_12_0'=0);
    [recv_rv_21_0] pkt_valid_21_0=true & pkt_type_21_0=TYPE_RV & pkt_term_21_0>term_1 & time_21_0 >= delay -> (pkt_valid_12_0'=true) & (pkt_type_12_0'=TYPE_RVR) & (pkt_term_12_0'=0) & (pkt_success_12_0'=true) & (time_12_0'=0);
    [recv_rvr_12_0] pkt_valid_12_0=true & pkt_type_12_0=TYPE_RVR & time_12_0 >= delay -> (pkt_valid_12_0'=false) & (pkt_type_12_0'=0) & (pkt_term_12_0'=0) & (pkt_success_12_0'=false) & (time_12_0'=0);

    [recv_rv_12_1] pkt_valid_12_1=true & pkt_type_12_1=TYPE_RV & time_12_1 >= delay -> (pkt_valid_12_1'=false);
    // TODO: should choose a empty slot to use (currently directly use the same slot)
    [recv_rv_21_1] pkt_valid_21_1=true & pkt_type_21_1=TYPE_RV & pkt_term_21_1<=term_1 & time_21_1 >= delay -> (pkt_valid_12_1'=true) & (pkt_type_12_1'=TYPE_RVR) & (pkt_term_12_1'=0) & (pkt_success_12_1'=false) & (time_12_1'=0);
    [recv_rv_21_1] pkt_valid_21_1=true & pkt_type_21_1=TYPE_RV & pkt_term_21_1>term_1 & time_21_1 >= delay -> (pkt_valid_12_1'=true) & (pkt_type_12_1'=TYPE_RVR) & (pkt_term_12_1'=0) & (pkt_success_12_1'=true) & (time_12_1'=0);
    [recv_rvr_12_1] pkt_valid_12_1=true & pkt_type_12_1=TYPE_RVR & time_12_1 >= delay -> (pkt_valid_12_1'=false) & (pkt_type_12_1'=0) & (pkt_term_12_1'=0) & (pkt_success_12_1'=false) & (time_12_1'=0);

endmodule

module node1
    role_1 : [0..3] init FOLLOWER;
    term_1 : [0..MAX_TERM+1] init 0;
    election_time_1 : [0..ELECTION_TIMEOUT+1] init 0;

    voted_1_0 : bool init false;
    voted_1_1 : bool init false;

    [time] election_time_1<ELECTION_TIMEOUT -> (election_time_1'=election_time_1+1);
    [time] election_time_1=ELECTION_TIMEOUT -> (election_time_1'=election_time_1);
    [election_timeout_1] role_1!=LEADER & election_time_1=ELECTION_TIMEOUT & term_1<MAX_TERM -> (role_1'=CANDIDATE) & (term_1'=term_1+1) & (election_time_1'=0) & (voted_1_0'=false) & (voted_1_1'=false);
    [election_timeout_terminate_1] election_time_1=ELECTION_TIMEOUT & term_1=MAX_TERM -> (term_1'=term_1) & (election_time_1'=0);

    [recv_rv_21_0] pkt_term_21_0>term_1 -> (term_1'=max(term_1, pkt_term_21_0)) & (role_1'=FOLLOWER) & (election_time_1'=0);
    [recv_rv_21_0] pkt_term_21_0<=term_1 -> true;
    // hack elected leader
    [recv_rvr_21_0] role_1=CANDIDATE & pkt_success_21_0=true -> (voted_1_1'=true) & (role_1'=LEADER);
    [recv_rvr_21_0] role_1=CANDIDATE & pkt_success_21_0=false -> true;

    [recv_rv_21_1] pkt_term_21_1>term_1 -> (term_1'=max(term_1, pkt_term_21_1)) & (role_1'=FOLLOWER) & (election_time_1'=0);
    [recv_rv_21_1] pkt_term_21_1<=term_1 -> true;
    // hack elected leader
    [recv_rvr_21_1] role_1=CANDIDATE & pkt_success_21_1=true -> (voted_1_1'=true) & (role_1'=LEADER);
    [recv_rvr_21_1] role_1=CANDIDATE & pkt_success_21_1=false -> true;

endmodule

module wire21=wire12[
    pkt_valid_12_0=pkt_valid_21_0, pkt_type_12_0=pkt_type_21_0, pkt_term_12_0=pkt_term_21_0, pkt_success_12_0=pkt_success_21_0, time_12_0=time_21_0,
    pkt_valid_12_1=pkt_valid_21_1, pkt_type_12_1=pkt_type_21_1, pkt_term_12_1=pkt_term_21_1, pkt_success_12_1=pkt_success_21_1, time_12_1=time_21_1,
    pkt_valid_21_0=pkt_valid_12_0, pkt_type_21_0=pkt_type_12_0, pkt_term_21_0=pkt_term_12_0, pkt_success_21_0=pkt_success_12_0, time_21_0=time_12_0,
    pkt_valid_21_1=pkt_valid_12_1, pkt_type_21_1=pkt_type_12_1, pkt_term_21_1=pkt_term_12_1, pkt_success_21_1=pkt_success_12_1, time_21_1=time_12_1,
    term_1=term_2, term_2=term_1, election_timeout_1=election_timeout_2, 
    recv_rv_12_0=recv_rv_21_0, recv_rv_21_0=recv_rv_12_0, recv_rvr_12_0=recv_rvr_21_0,
    recv_rv_12_1=recv_rv_21_1, recv_rv_21_1=recv_rv_12_1, recv_rvr_12_1=recv_rvr_21_1
] endmodule

module node2=node1[
    role_1=role_2, term_1=term_2, 
    voted_1_0=voted_2_1, 
    voted_1_1=voted_2_0, 
    pkt_term_21_0=pkt_term_12_0, recv_rv_21_0=recv_rv_12_0, recv_rvr_21_0=recv_rvr_12_0, 
    pkt_term_21_1=pkt_term_12_1, recv_rv_21_1=recv_rv_12_1, recv_rvr_21_1=recv_rvr_12_1, 
    election_time_1=election_time_2, election_timeout_1=election_timeout_2, election_timeout_terminate_1=election_timeout_terminate_2
] endmodule

// rewards (to calculate expected number of steps)
rewards "steps"
    true : 1;
endrewards

label "recv_rv_12_0_cond1" = role_1!=LEADER;
label "recv_rv_12_0_cond2" = election_time_1=ELECTION_TIMEOUT;
label "recv_rv_12_0_cond3" = term_1<MAX_TERM;

label "elected_1" = role_1=LEADER;
label "elected_2" = role_2=LEADER;
