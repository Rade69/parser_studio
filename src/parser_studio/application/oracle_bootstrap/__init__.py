# Application: oracle_bootstrap.
# Posjeduje: BootstrapOracle, ConfirmOracle use cases.
# Smije zavisiti samo od: domain, ports.
# Ne zna za: adapters, presentation, contract, SQLite.
"""Oracle bootstrap use cases.

V3_2 §44 D3 — Human verification. Oracle (D1) + Oracle → Candidate (D2)
se sastavljaju u dva use case-a:

- BootstrapOracle: pokreni oracle na fajlu, dohvati OraclePayload,
  pozovi OracleCandidateProducer, vrati ExtractionDraft sa oracle
  kandidatima.

- ConfirmOracle: korisnik accept/reject oracle vrijednost. accept
  emituje ORACLE_CONFIRMED + USER_CONFIRMED event (oracle postaje
  Gold). reject emituje ORACLE_REJECTED event (bez confirmed value).

Stari parser NIJE automatski istina (V3 §23). ConfirmOracle je
TAJ koji odlučuje.
"""