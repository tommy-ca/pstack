----------------------- MODULE WikiRawImmutability -----------------------
EXTENDS Naturals, TLC
CONSTANTS Names, Blobs, Empty
VARIABLES raw, original

vars == <<raw, original>>

Init ==
    /\ raw = [n \in Names |-> Empty]
    /\ original = [n \in Names |-> Empty]

Create(n, b) ==
    /\ n \in Names
    /\ b \in Blobs
    /\ raw[n] = Empty
    /\ raw' = [raw EXCEPT ![n] = b]
    /\ original' = [original EXCEPT ![n] = b]

Replay(n, b) ==
    /\ n \in Names
    /\ b \in Blobs
    /\ raw[n] = b
    /\ UNCHANGED vars

Next == \E n \in Names, b \in Blobs : Create(n, b) \/ Replay(n, b)
Spec == Init /\ [][Next]_vars
NeverOverwrite == \A n \in Names : raw[n] = original[n]
TypeOK == raw \in [Names -> (Blobs \cup {Empty})]
        /\ original \in [Names -> (Blobs \cup {Empty})]
=============================================================================
