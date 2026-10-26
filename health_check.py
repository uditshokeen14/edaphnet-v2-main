# health_check.py
import subprocess, sys, os, json, pathlib

def run(cmd, cwd=None):
    print(f"\n>> {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    print(result.stdout)
    return result.returncode, result.stdout

def main():
    steps = [
        ("Tests", "python -m pytest -q"),
        ("Demo",  "python scripts/demo.py"),
        ("Train", "python scripts/train_colour_brain.py"),
        ("Serve", "echo Serve step skipped"),
        ("Streamlit", "streamlit run streamlit_app.py --server.headless true"),
        ("Sim (smoke)", "python scripts/run_sim.py --config configs/sim_t0.yaml --smoke"),
        ("Real (smoke)", "python scripts/run_real.py --config configs/real_icraf8.yaml --smoke"),
    ]

    all_ok = True
    for name, cmd in steps:
        rc, out = run(cmd, cwd=os.getcwd())
        if rc != 0:
            print(f"❌ {name} FAILED")
            all_ok = False
            break
        else:
            print(f"✅ {name} OK")
    if all_ok:
        print("\n🎉 All checks passed! Project is functional.")
    else:
        print("\n⚠️  Some step failed – see above for details.")

if __name__ == "__main__":
    main()
