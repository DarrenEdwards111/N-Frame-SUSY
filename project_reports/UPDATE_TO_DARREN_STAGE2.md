# Update To Darren: Stage 2 CMS Open Data Boundary Test

We have now independently downloaded a small public CMS Open Data subset, including three real 2016 collision control samples and two official CMS simulated SUSY-like signal samples.

The samples are:

- real CMS MET collision data
- real CMS JetHT collision data
- real CMS SingleMuon collision data
- official CMS T5Wg SUSY signal simulation
- official CMS HToAA4B SUSY-like signal simulation

The first Stage 2 goal was to extract event-level variables and fit an N-Frame boundary score. This is not a SUSY discovery test. It is a validation test of whether the boundary variables identify known SUSY-like event structures before applying the model back to real collision data only.

Using Python/uproot, all five ROOT files opened successfully and all had readable `Events` trees. The lightweight extraction produced 308,184 event rows. However, because these are MiniAOD EDM files, Python/uproot could only extract jet-level variables reliably. MET, leptons, standard b-tags, displacement, and lifetime variables still require CMSSW.

With the available jet/reconstruction-only boundary score, the T5Wg simulated SUSY sample separated very strongly from all three real collision controls. Its mean boundary score was 2.1195, compared with -0.1925 for MET, 0.6884 for JetHT, and -0.3426 for SingleMuon. About 50.4% of T5Wg events landed in the global top 5% boundary-score tail.

The HToAA4B sample did not separate cleanly with this jet-only score. That is useful rather than surprising: it suggests that this sample probably needs b-tags, substructure, or the full CMSSW object extraction to become visible to the boundary model.

This Stage 2 result is consistent with the earlier signal-region finding in a limited way. Previously, rare/topology-stressed public ATLAS/CMS signal regions had higher anomaly magnitudes. Here, a known hard SUSY-like simulated sample also concentrates strongly in high event-level boundary score. That supports the trace-level boundary-stress interpretation, but only as a validation of the scoring direction.

The next required step is CMSSW extraction. A run guide and filelists have been prepared. Once Docker/CMSSW is available, we can extract MET, leptons, b-tags, and better reconstruction variables, then re-fit the full N-Frame event-level boundary model.

Careful framing:

> We have not found SUSY, and this does not show that CERN missed SUSY. What we have shown is that a partial N-Frame boundary score identifies a known SUSY-like simulated topology, and this supports further testing of the boundary-trace hypothesis with full CMSSW features.

