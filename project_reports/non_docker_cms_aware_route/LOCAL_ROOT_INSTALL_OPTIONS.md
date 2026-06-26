# Local ROOT Install Options

## Current Status

Conda is available by absolute path:

```powershell
D:\Anaconda\Scripts\conda.exe --version
```

Observed result:

```text
conda 25.5.1
```

`mamba` was not found at:

```text
D:\Anaconda\Scripts\mamba.exe
```

`conda` is not currently on the normal PowerShell PATH, but it can be called directly.

## Safe Principle

Do not install ROOT into the main/base Anaconda environment. ROOT is large and can change many dependencies. If we try it, use a separate environment.

Recommended environment name:

```text
nframe-root
```

## Possible Commands

Do not run these automatically without confirmation:

```powershell
& "D:\Anaconda\Scripts\conda.exe" create -n nframe-root -c conda-forge python=3.11 root uproot awkward pandas numpy scipy matplotlib -y
& "D:\Anaconda\Scripts\conda.exe" activate nframe-root
python -c "import ROOT; print(ROOT.gROOT.GetVersion())"
```

If activation is awkward in this PowerShell session, use:

```powershell
& "D:\Anaconda\Scripts\conda.exe" run -n nframe-root python -c "import ROOT; print(ROOT.gROOT.GetVersion())"
```

## Important Limitation

Local ROOT/PyROOT alone may still not provide the CMS MiniAOD/FWLite dictionaries needed to unpack `slimmedMETs`, `slimmedMuons`, `slimmedElectrons`, `EventAuxiliary`, and `TriggerResults` as physics objects.

So this route is worth trying, but success is not guaranteed. It may let us inspect ROOT files through PyROOT, while still failing on CMS EDM object interpretation.

## Recommendation

Ask before creating the environment. It is safe in principle because it is separate from base Anaconda, but it may take time and disk space.

