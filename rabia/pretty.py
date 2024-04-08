# TODO: 
# 1. Support response with decided
# 2. Store messages from future rounds
import itertools
    

buf_size = 3
num_nodes = 2
quorum_size = num_nodes//2+1
log_size = 1
queue_size = 2
max_round = 2


def valid_quorum_same_as(target_variable, other_variables, quorum_size):
    return '|'.join(['(' + '&'.join([f"{v}!=INVALID&{v}={target_variable}" for v in quorums]) + ')' for quorums in itertools.combinations(other_variables, quorum_size-1)])

def valid_quorum_proposal_same_as(code_nid, same_as, all_nid_list, seq, quorum_size):
    return valid_quorum_same_as(f"n{code_nid}_proposal_{seq}_n{same_as}", [f"n{code_nid}_proposal_{seq}_n{j}" for j in all_nid_list if j != same_as], quorum_size)

def valid_quorum_state_same_as(code_nid, same_as, all_nid_list, seq, quorum_size):
    return valid_quorum_same_as(f"n{code_nid}_state_ts_{seq}_n{same_as}", [f"n{code_nid}_state_ts_{seq}_n{j}" for j in all_nid_list if j != same_as], quorum_size)

def valid_quorum_vote_same_as(code_nid, same_as, all_nid_list, seq, quorum_size):
    return valid_quorum_same_as(f"n{code_nid}_vote_ts_{seq}_n{same_as}", [f"n{code_nid}_vote_ts_{seq}_n{j}" for j in all_nid_list if j != same_as], quorum_size)

def quorum_valid(variables, quorum_size):
    return '|'.join(['(' + '&'.join([f"{v}!=INVALID" for v in quorums]) + ')' for quorums in itertools.combinations(variables, quorum_size)])

def quorum_valid_proposal(code_nid, all_nid_list, seq, quorum_size):
    return quorum_valid([f"n{code_nid}_proposal_{seq}_n{j}" for j in all_nid_list], quorum_size)

def quorum_valid_state(code_nid, all_nid_list, seq, quorum_size):
    return quorum_valid([f"n{code_nid}_state_ts_{seq}_n{j}" for j in all_nid_list], quorum_size)

def quorum_valid_vote(code_nid, all_nid_list, seq, quorum_size):
    return quorum_valid([f"n{code_nid}_vote_ts_{seq}_n{j}" for j in all_nid_list], quorum_size)

def all_valid_vote_are_question(code_nid, all_nid_list, seq):
    return f"{'&'.join([f'n{code_nid}_vote_ts_{seq}_n{j}!=INVALID&n{code_nid}_vote_ts_{seq}_n{j}=QUES_VOTE' for j in all_nid_list])}"
    
    
def reset_state_and_vote(code_nid, all_nid_list, seq, except_nid=None):
    return f"""{'&'.join([f"(n{code_nid}_state_ts_{seq}_n{j}'=INVALID)&(n{code_nid}_vote_ts_{seq}_n{j}'=INVALID)" for j in all_nid_list if j != except_nid])}"""

prologue_code = f"""// Rabia Algorithm


dtmc

const NUM_NODES = {num_nodes};
const QUORUM_SIZE = {quorum_size};
const BUF_SIZE = {buf_size};
const MAX_TS = 2;
const QUEUE_SIZE = {queue_size};
const LOG_SIZE = {log_size};
const MAX_ROUND = {max_round};

const p0_bc_cmd_stage = 0;
const p1_stage = 1;
const p2s_stage = 2;
const p2v_stage = 3;
const decided = 4;
const NUM_STATES = 5

const cmd_request = 0;
const cmd_proposal = 1;
const cmd_state = 2;
const cmd_vote = 3;
const NUM_CMD_TYPES = 4;

const INVALID=-1;
const BOT = -2;
const QUES_VOTE = -3;

const MIN_VOTE_VALUE=-3;
const MIN_TS_VALUE=-3;

"""

node_code = [f"""
module node{_}
    // states
    n{_}_seq : [0..LOG_SIZE] init 0;
    /// p1 stage""" + ''.join([f"""
    n{_}_stage_{i} : [0..NUM_STATES] init p0_bc_cmd_stage;
    n{_}_pq_valid_{i} : bool init {"true" if i == 0 else "false"};
    n{_}_pq_ts_{i} : [0..MAX_TS] init {(1 if _ < 2 else 2) if i == 0 else 0};""" for i in range(queue_size)]) + ''.join([f"""
    n{_}_log_ts_{i} : [MIN_TS_VALUE..LOG_SIZE] init INVALID; """ for i in range(log_size)]) + """
    /// p2 stage""" + ''.join([f"""
    n{_}_round_{i} : [0..MAX_ROUND] init 0; """ for i in range(log_size)]) + ''.join([f"""
    n{_}_proposal_{seq}_n{nid} : [MIN_TS_VALUE..MAX_TS] init INVALID;
    n{_}_state_ts_{seq}_n{nid} : [MIN_TS_VALUE..MAX_TS] init INVALID;
    n{_}_vote_ts_{seq}_n{nid} : [MIN_VOTE_VALUE..MAX_TS] init INVALID;""" for seq, nid in itertools.product(range(log_size), range(num_nodes))]) + f"""

    // pkt to send
    n{_}_send_ready : bool init false; // ready means not yet sent
    n{_}_send_is_broadcast : bool init false;
    n{_}_send_type : [0..NUM_CMD_TYPES] init 0;
    n{_}_send_seq : [0..LOG_SIZE] init 0;
    n{_}_send_round : [0..MAX_ROUND] init 0;
    n{_}_send_cmd_ts : [MIN_TS_VALUE..MAX_TS] init 0;

    // pkt received
    n{_}_recv_ready : bool init false; // ready means received
    n{_}_recv_from : [0..NUM_NODES] init 0;
    n{_}_recv_type : [0..NUM_CMD_TYPES] init 0;
    n{_}_recv_seq : [0..LOG_SIZE] init 0;
    n{_}_recv_round : [0..MAX_ROUND] init 0;
    n{_}_recv_cmd_ts : [MIN_TS_VALUE..MAX_TS] init 0;""" + """
    
    // Try on each queue slot and execute if the slot has min ts""" + ''.join([f"""
    [n{_}_propose_next_command_for_seq{seq}_usingqueue{qid}] n{_}_stage_{seq}=p0_bc_cmd_stage & n{_}_send_ready=false & n{_}_seq={seq} & n{_}_pq_valid_{qid}=true & {'&'.join([f"(!n{_}_pq_valid_{j}|n{_}_pq_ts_{j}>=n{_}_pq_ts_{qid})" for j in range(queue_size)])} -> \
        (n{_}_stage_{seq}'=p1_stage) & (n{_}_send_ready'=true) & (n{_}_send_is_broadcast'=true) & (n{_}_send_type'=cmd_proposal) & (n{_}_send_cmd_ts'=n{_}_pq_ts_{qid}) & (n{_}_proposal_{seq}_n{_}'=n{_}_pq_ts_{qid});""" for qid, seq in itertools.product(range(queue_size), range(log_size))]) + f"""
    
    // Process when a Proposal pkt is ready.""" + ''.join([f"""
    // Drop a message if it is not at a correct stage (TODO: add round)
    [n{_}_drop_recv_if_proposal_in_p1] n{_}_stage_{seq}=p1_stage & n{_}_recv_ready=true & n{_}_recv_type!=cmd_proposal -> (n{_}_recv_ready'=false);""" for seq in range(log_size)]) + ''.join([f"""
    // Try to receive the proposal from node {nid} for seq {seq}.
    [n{_}_process_proposal_from_n{nid}_for_seq{seq}] n{_}_stage_{seq}=p1_stage & n{_}_recv_ready=true & n{_}_recv_from={nid} & n{_}_recv_type=cmd_proposal & n{_}_recv_seq={seq}-> \
        (n{_}_recv_ready'=false) & (n{_}_proposal_{seq}_n{nid}'=n{_}_recv_cmd_ts);
    // Try to assign the state using the proposal from node {nid} for seq {seq} when we have enough proposals.
    [n{_}_process_proposal_assign_state_{seq}_using_n{nid}] n{_}_stage_{seq}=p1_stage & n{_}_send_ready=false & ({quorum_valid_proposal(_, range(num_nodes), seq, quorum_size)}) & ({valid_quorum_proposal_same_as(_, nid, range(num_nodes), seq, quorum_size)}) -> \
        (n{_}_state_ts_{seq}_n{_}'=n{_}_proposal_{seq}_n{nid}) & (n{_}_stage_{seq}'=p2s_stage) & (n{_}_send_ready'=true) & (n{_}_send_is_broadcast'=true) & (n{_}_send_type'=cmd_state) & (n{_}_send_cmd_ts'=n{_}_proposal_{seq}_n{nid});
    // We got enough proposals but no enough same proposals, thus assigning BOT. (TODO: change the action name, we may not need `_using_n{nid}` here.)
    [n{_}_process_proposal_assign_state_{seq}_using_n{nid}] n{_}_stage_{seq}=p1_stage & n{_}_send_ready=false & ({quorum_valid_proposal(_, range(num_nodes), seq, quorum_size)}) & !({valid_quorum_proposal_same_as(_, nid, range(num_nodes), seq, quorum_size)}) -> \
        (n{_}_state_ts_{seq}_n{_}'=BOT) & (n{_}_stage_{seq}'=p2s_stage) & (n{_}_send_ready'=true) & (n{_}_send_is_broadcast'=true) & (n{_}_send_type'=cmd_state) & (n{_}_send_cmd_ts'=BOT);""" for seq, nid in itertools.product(range(log_size), range(num_nodes))]) + f"""

    // Process when a State pkt is ready.""" + ''.join([f"""
    // Drop a message if it is not at a correct stage (TODO: add round)
    [n{_}_drop_recv_if_state_in_p2s] n{_}_stage_{seq}=p2s_stage & n{_}_recv_ready=true & n{_}_recv_type!=cmd_state -> (n{_}_recv_ready'=false);""" for seq in range(log_size)]) + ''.join([f"""
    // Try to receive the state from node {nid} for seq {seq}.
    [n{_}_process_state_from_n{nid}_for_seq_{seq}] n{_}_stage_{seq}=p2s_stage & n{_}_recv_ready=true & n{_}_recv_from={nid} & n{_}_recv_type=cmd_state & n{_}_recv_seq={seq} -> \
        (n{_}_recv_ready'=false) & (n{_}_state_ts_{seq}_n{nid}'=n{_}_recv_cmd_ts);
    // Try to assign the state using the state from node {nid} for seq {seq} when we have enough states.
    [n{_}_process_state_assign_vote_{seq}_using_n{nid}] n{_}_stage_{seq}=p2s_stage & n{_}_send_ready=false & ({quorum_valid_state(_, range(num_nodes), seq, quorum_size)}) &  ({valid_quorum_state_same_as(_, nid, range(num_nodes), seq, quorum_size)}) -> \
        (n{_}_vote_ts_{seq}_n{_}'=n{_}_state_ts_{seq}_n{nid}) & (n{_}_stage_{seq}'=p2v_stage) & (n{_}_send_ready'=true) & (n{_}_send_is_broadcast'=true) & (n{_}_send_type'=cmd_vote) & (n{_}_send_cmd_ts'=n{_}_state_ts_{seq}_n{nid});
    // We got enough states but no enough same states, thus assigning BOT.
    [n{_}_process_state_assign_vote_{seq}_using_n{nid}] n{_}_stage_{seq}=p2s_stage & n{_}_send_ready=false & ({quorum_valid_state(_, range(num_nodes), seq, quorum_size)}) & !({valid_quorum_state_same_as(_, nid, range(num_nodes), seq, quorum_size)}) -> \
        (n{_}_vote_ts_{seq}_n{_}'=QUES_VOTE) & (n{_}_stage_{seq}'=p2v_stage) & (n{_}_send_ready'=true) & (n{_}_send_is_broadcast'=true) & (n{_}_send_type'=cmd_vote) & (n{_}_send_cmd_ts'=BOT);""" for seq, nid in itertools.product(range(log_size), range(num_nodes))]) + f"""

    // Process when a Vote pkt is ready.""" + ''.join([f"""
    // Drop a message if it is not at a correct stage (TODO: add round)
    [n{_}_drop_recv_if_vote_in_p2v_for_seq{seq}] n{_}_stage_{seq}=p2v_stage & n{_}_recv_ready=true & n{_}_recv_type!=cmd_vote -> (n{_}_recv_ready'=false);""" for seq in range(log_size)]) + ''.join([f"""
    // Try to receive the vote from node {nid} for seq {seq}.
    [n{_}_process_vote_from_n{nid}_for_seq{seq}] n{_}_stage_{seq}=p2v_stage & n{_}_recv_ready=true & n{_}_recv_from={nid} & n{_}_recv_type=cmd_vote & n{_}_recv_seq={seq} -> \
        (n{_}_recv_ready'=false) & (n{_}_vote_ts_{seq}_n{nid}'=n{_}_recv_cmd_ts);
    // Try to use the vote from node {nid} for seq {seq} when we have enough same votes, and return.
    [n{_}_process_vote_for_seq{seq}_using_n{nid}] n{_}_stage_{seq}=p2v_stage & n{_}_seq=LOG_SIZE-1 n{_}_send_ready=false & (n{_}_vote_ts_{seq}_n{nid}!=INVALID&n{_}_vote_ts_{seq}_n{nid}!=QUES_VOTE) & ({quorum_valid_vote(_, range(num_nodes), seq, quorum_size)}) &  ({valid_quorum_vote_same_as(_, nid, range(num_nodes), seq, quorum_size)}) -> \
        (n{_}_log_ts_{seq}'=n{_}_vote_ts_{seq}_n{nid}) & (n{_}_stage_{seq}'=decided) & {reset_state_and_vote(_, range(num_nodes), seq=seq, except_nid=_)};
    // We don't have enough same votes, but we have the vote from {nid} that is not QUES_VOTE.
    [n{_}_process_vote_for_seq{seq}_using_n{nid}] n{_}_stage_{seq}=p2v_stage & n{_}_send_ready=false & (n{_}_vote_ts_{seq}_n{nid}!=INVALID&n{_}_vote_ts_{seq}_n{nid}!=QUES_VOTE) & ({quorum_valid_vote(_, range(num_nodes), seq, quorum_size)}) & !({valid_quorum_vote_same_as(_, nid, range(num_nodes), seq, quorum_size)}) -> \
        (n{_}_state_ts_{seq}_n{_}'=n{_}_vote_ts_{seq}_n{nid})  & (n{_}_vote_ts_{seq}_n{_}'=INVALID) & (n{_}_stage_{seq}'=p2s_stage) & (n{_}_send_ready'=true) & (n{_}_send_is_broadcast'=true) & (n{_}_send_type'=cmd_state) & (n{_}_send_cmd_ts'=n{_}_state_ts_{seq}_n{nid}) & {reset_state_and_vote(_, range(num_nodes), seq=seq, except_nid=_)};
    // We only got QUES_VOTE, let god decides.
    [n{_}_process_vote_for_seq{seq}_using_n{nid}] n{_}_stage_{seq}=p2v_stage & n{_}_send_ready=false & ({quorum_valid_vote(_, range(num_nodes), seq, quorum_size)}) & {all_valid_vote_are_question(_, range(num_nodes), seq)} -> \
        (n{_}_state_ts_{seq}_n{_}'=BOT)                        & (n{_}_vote_ts_{seq}_n{_}'=INVALID) & (n{_}_stage_{seq}'=p2s_stage) & (n{_}_send_ready'=true) & (n{_}_send_is_broadcast'=true) & (n{_}_send_type'=cmd_state) & (n{_}_send_cmd_ts'=BOT)                        & {reset_state_and_vote(_, range(num_nodes), seq=seq, except_nid=_)};
    [n{_}_process_vote_for_seq{seq}_using_n{nid}] n{_}_stage_{seq}=p2v_stage & n{_}_send_ready=false & ({quorum_valid_vote(_, range(num_nodes), seq, quorum_size)}) & {all_valid_vote_are_question(_, range(num_nodes), seq)} -> \
        (n{_}_state_ts_{seq}_n{_}'=n{_}_state_ts_{seq}_n{nid}) & (n{_}_vote_ts_{seq}_n{_}'=INVALID) & (n{_}_stage_{seq}'=p2s_stage) & (n{_}_send_ready'=true) & (n{_}_send_is_broadcast'=true) & (n{_}_send_type'=cmd_state) & (n{_}_send_cmd_ts'=n{_}_state_ts_{seq}_n{nid}) & {reset_state_and_vote(_, range(num_nodes), seq=seq, except_nid=_)};""" for seq, nid in itertools.product(range(log_size), range(num_nodes))]) + """
    
    

    // Send when a pkt is ready; Recv when a pkt is ready.""" + ''.join([f"""
    [recv_{j}{_}_{bid}] n{_}_recv_ready=false -> \
        (n{_}_recv_ready'=true) & (n{_}_recv_from'={j}) & (n{_}_recv_type'=w{j}{_}_pkt_type_{bid}) & (n{_}_recv_seq'=w{j}{_}_pkt_seq_{bid}) & (n{_}_recv_round'=w{j}{_}_pkt_round_{bid}) & (n{_}_recv_cmd_ts'=w{j}{_}_pkt_cmd_ts_{bid});
    [send_{_}{j}_{bid}] n{_}_send_ready=true & n{_}_send_is_broadcast=false -> (n{_}_send_ready'=false);""" for bid, j in itertools.product(range(buf_size), range(num_nodes)) if j != _]) + ''.join([f"""
    [n{_}_send_broadcast] n{_}_send_ready=true & n{_}_send_is_broadcast=true -> (n{_}_send_ready'=false);""" for i in range(buf_size)]) + """

endmodule
"""
for _ in range(num_nodes)]

# Packet Types:
# - <Request, cmd: Command>
# - <Proposal, q: Command>
# - <State, round, state: Command|BOT>
# - <Vote, round, vote: Command|QUES_VOTE>
wire_code = f"""
module wire01""" + ''.join([f"""
    // pkt slot {i}
    w01_pkt_valid_{i} : bool init false;
    w01_pkt_type_{i} : [0..NUM_CMD_TYPES] init 0;
    w01_pkt_seq_{i} : [0..LOG_SIZE] init 0;
    w01_pkt_round_{i} : [0..MAX_ROUND] init 0;
    w01_pkt_cmd_ts_{i} : [MIN_TS_VALUE..MAX_TS] init 0;""" for i in range(buf_size)]) + ''.join([f"""
    [n0_send_broadcast] n0_send_ready=true & n0_send_is_broadcast=true & w01_pkt_valid_{i}=false -> \
        (w01_pkt_valid_{i}'=true) & (w01_pkt_type_{i}'=n0_send_type) & (w01_pkt_seq_{i}'=n0_send_seq) & (w01_pkt_round_{i}'=n0_send_round) & (w01_pkt_cmd_ts_{i}'=n0_send_cmd_ts);
    [send_01_{i}] n0_send_ready=true & n0_send_is_broadcast=false & w01_pkt_valid_{i} = false & n0_send_ready=true -> \
        (w01_pkt_valid_{i}'=true) & (w01_pkt_type_{i}'=n0_send_type) & (w01_pkt_seq_{i}'=n0_send_seq) & (w01_pkt_round_{i}'=n0_send_round) & (w01_pkt_cmd_ts_{i}'=n0_send_cmd_ts);
    [recv_01_{i}] n0_recv_ready=false & w01_pkt_valid_{i} = true -> (w01_pkt_valid_{i}'=false);""" for i in range(buf_size)]) + """

endmodule
"""

# node_variables_list = [
#     [
#         f"n{nid}_stage", f"n{nid}_seq", 
#         *[f"n{nid}_pq_valid_{i}" for i in range(queue_size)], 
#         *[f"n{nid}_pq_ts_{i}" for i in range(queue_size)], 
#         *[f"n{nid}_log_ts_{i}" for i in range(log_size)], 
#         *[f"n{nid}_round_{i}" for i in range(log_size)],
#         *[f"n{nid}_my_proposal_{i}" for i in range(log_size)],
#         *[f"n{nid}_state_ts_{i}" for i in range(log_size)],
#         *[f"n{nid}_vote_ts_{i}" for i in range(log_size)],
#         *[f"n{nid}_proposal_{i}_n{j}" for i, j in itertools.product(range(log_size), range(num_nodes))],
#         *[f"n{nid}_state_ts_{i}_n{j}" for i, j in itertools.product(range(log_size), range(num_nodes))],
#         *[f"n{nid}_vote_ts_{i}_n{j}" for i, j in itertools.product(range(log_size), range(num_nodes))],
#         *[f"n{nid}_send_ready", f"n{nid}_send_is_broadcast", f"n{nid}_send_type", f"n{nid}_send_seq", f"n{nid}_send_round", f"n{nid}_send_cmd_ts"],
#         *[f"n{nid}_recv_ready", f"n{nid}_recv_from", f"n{nid}_recv_type", f"n{nid}_recv_seq", f"n{nid}_recv_round", f"n{nid}_recv_cmd_ts"],
#         *[f"n{nid}_propose_next_command_for_seq{seq}_usingqueue{i}" for i, seq in itertools.product(range(queue_size), range(log_size))],
#         *[f"n{nid}_process_proposal_from_n{j}_for_seq{i}" for i, j in itertools.product(range(log_size), range(num_nodes)) if j != nid],
#         *[f"n{nid}_process_proposal_assign_state_{i}_using_n{j}" for i, j in itertools.product(range(log_size), range(num_nodes))],
#         *[f"n{nid}_process_state_from_n{j}_for_seq_{i}" for i, j in itertools.product(range(log_size), range(num_nodes)) if j != nid],
#         *[f"n{nid}_process_state_assign_vote_{i}_using_n{j}" for i, j in itertools.product(range(log_size), range(num_nodes))],
#         *[f"n{nid}_process_vote_from_n{j}_for_seq{i}" for i, j in itertools.product(range(log_size), range(num_nodes)) if j != nid],
#         *[f"n{nid}_process_vote_for_seq{i}_using_n{j}" for i, j in itertools.product(range(log_size), range(num_nodes))],
#         *[f"recv_{j}{nid}_{bid}" for bid, j in itertools.product(range(buf_size), range(num_nodes)) if j != nid],
#         *list(itertools.chain(*[[
#             f"w{j}{nid}_pkt_valid_{bid}", f"w{j}{nid}_pkt_type_{bid}", f"w{j}{nid}_pkt_seq_{bid}", f"w{j}{nid}_pkt_round_{bid}", f"w{j}{nid}_pkt_cmd_ts_{bid}",
#             f"w{nid}{j}_pkt_valid_{bid}", f"w{nid}{j}_pkt_type_{bid}", f"w{nid}{j}_pkt_seq_{bid}", f"w{nid}{j}_pkt_round_{bid}", f"w{nid}{j}_pkt_cmd_ts_{bid}",
#         ] for bid, j in itertools.product(range(buf_size), range(num_nodes)) if j != nid])),
#         f"n{nid}_send_broadcast", 
#         *[f"send_{nid}{j}_{i}" for i, j in itertools.product(range(buf_size), range(num_nodes)) if j != nid],
#     ]
#     for nid in range(num_nodes)
# ]

wire_variables_list = {
    (i, j): [
        f"n{i}_send_broadcast", 
        *list(itertools.chain(*[[
            f"w{i}{j}_pkt_valid_{bid}", f"w{i}{j}_pkt_type_{bid}", f"w{i}{j}_pkt_seq_{bid}", f"w{i}{j}_pkt_round_{bid}", f"w{i}{j}_pkt_cmd_ts_{bid}", 
            f"send_{i}{j}_{bid}", f"recv_{i}{j}_{bid}"] for bid in range(buf_size) if i != j])),
        f"n{i}_send_ready",
        f"n{i}_send_is_broadcast",
        f"n{i}_send_type",
        f"n{i}_send_seq",
        f"n{i}_send_round",
        f"n{i}_send_cmd_ts",
    ]
    for i, j in itertools.product(range(num_nodes), range(num_nodes))
}

module_rename_codes = [
    # f"module node1 = node0[" + ','.join([f'{name0}={name1}' for name0, name1 in zip(node_variables_list[0], node_variables_list[1])]) + f"] endmodule",
    *[f"module wire{i}{j} = wire01[" + ','.join([f'{name0}={name1}' for name0, name1 in zip(wire_variables_list[(0,1)], wire_variables_list[(i,j)])]) + f"""] endmodule
     """ for i, j in itertools.product(range(num_nodes), range(num_nodes)) if i != j and not (i==0 and j==1)],
]

epilogue_code = """
// rewards (to calculate expected number of steps)
rewards "steps"
    true : 1;
endrewards""" + ''.join([f"""
label "n{_}_decided_log_seq{i}" = n{_}_log_ts_{i} != INVALID;
label "n{_}_decided_log_seq{i}_non_bot" = n{_}_log_ts_{i} != INVALID & n{_}_log_ts_{i} != BOT;""" for _, i in itertools.product(range(num_nodes), range(log_size))]) + """

"""

code = ''.join([prologue_code, '\n'.join(node_code), wire_code, '\n'.join(module_rename_codes), epilogue_code])
# print(code)
open('rabia.nm', 'w').write(code)