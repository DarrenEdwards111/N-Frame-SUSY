# Rare-Row Rebuilt Boundary Analysis

## Scope

This is exploratory model development. `B_rebuilt` uses label-derived cut-scale proxies for rare rows whose verified+imputed `B` collapsed to zero. These proxy values are not verified cut metadata.

## Key Data Facts

- Signal regions: 752
- Rare rows: 73
- Rare rows with proxy cut numbers: 73
- Nonzero rebuilt interaction rows: 73

## Rare vs Nonrare Magnitude Tests

```text
           outcome  rare_mean  nonrare_mean  difference      welch_p  rare_n  nonrare_n
    abs_Z_capped_3   2.013664      1.168257    0.845407 2.234799e-08      73        679
abs_Z_conservative   1.146650      0.634638    0.512012 8.844116e-05      73        679
       abs_Poisson   1.363982      0.940783    0.423199 1.819502e-03      73        679
        Z_capped_3   1.276763      0.013207    1.263555 5.942920e-07      73        679
```

## Interaction Models

```text
dataset            outcome   n  n_analyses      coef  p_value  cluster_p_value       r2    adj_r2                              note
 pooled     abs_Z_capped_3 752          40  0.075385 0.810247     8.959971e-01 0.187956  0.139851 exploratory proxy B for rare rows
  ATLAS     abs_Z_capped_3 555          32  2.124981 0.001865     1.841908e-06 0.175290  0.121367 exploratory proxy B for rare rows
    CMS     abs_Z_capped_3 197           8  3.904133 0.386422     1.960538e-15 0.123067  0.075920 exploratory proxy B for rare rows
 pooled         Z_capped_3 752          40 -0.406316 0.433635     1.778405e-02 0.138646  0.087621 exploratory proxy B for rare rows
  ATLAS         Z_capped_3 555          32 -0.316193 0.784201     6.029096e-01 0.147029  0.091258 exploratory proxy B for rare rows
    CMS         Z_capped_3 197           8 18.651556 0.006325     3.161004e-24 0.129316  0.082505 exploratory proxy B for rare rows
 pooled abs_Z_conservative 752          40  0.226861 0.283729     6.855899e-01 0.126710  0.074978 exploratory proxy B for rare rows
  ATLAS abs_Z_conservative 555          32  2.058997 0.000005     3.325605e-04 0.168499  0.114131 exploratory proxy B for rare rows
    CMS abs_Z_conservative 197           8  3.923595 0.221469     7.752704e-16 0.085271  0.036092 exploratory proxy B for rare rows
 pooled        abs_Poisson 752          40  0.287391 0.312927     6.512486e-01 0.106388  0.053452 exploratory proxy B for rare rows
  ATLAS        abs_Poisson 555          32  2.446556 0.000017     2.478526e-04 0.166937  0.112467 exploratory proxy B for rare rows
    CMS        abs_Poisson 197           8  4.479799 0.401413     2.504906e-13 0.042871 -0.008588 exploratory proxy B for rare rows
```

## Cross-Validation

```text
                scheme   n  n_train        r2      mae     rmse      corr
GroupKFold_by_analysis 752      752 -0.182320 0.885525 1.077060  0.017097
  ATLAS_train_CMS_test 197      555 -1.239597 0.980752 1.172139 -0.051344
  CMS_train_ATLAS_test 555      197 -0.193561 0.877446 1.119514  0.182511
```

## Interpretation

Weak exploratory signal: interaction is positive after rebuilding rare-row B, but robustness/CV is insufficient.

Do not claim SUSY discovery. Do not claim N-Frame confirmed. The stable result remains that rare/reconstruction-stressed topologies have larger residual magnitudes; the boundary interaction now depends on proxy label reconstruction and needs real HEPData/paper cut metadata.
