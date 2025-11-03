from pathlib import Path
import pandas as pd
import yaml
from src.core.backtest_runner import run_strategy


def scan_thresholds(buy_values=[0.2, 0.3, 0.4, 0.5], sell_values=[-0.2, -0.3, -0.4, -0.5]):
    results = []
    cfg_path = Path("config/settings.yaml")
    base_cfg = yaml.safe_load(cfg_path.read_text())

    for b in buy_values:
        for s in sell_values:
            base_cfg['confluence']['thresholds']['buy'] = b
            base_cfg['confluence']['thresholds']['sell'] = s
            cfg_path.write_text(yaml.dump(base_cfg))
            print(f"Testing buy={b}, sell={s}...")
            run_strategy()  # your backtest run
            # read latest metrics
            m = yaml.safe_load(Path("data/features/metrics_summary.json").read_text())
            results.append({"buy": b, "sell": s, **m})

    df = pd.DataFrame(results)
    df.to_csv("data/features/threshold_scan.csv", index=False)
    print(df)
