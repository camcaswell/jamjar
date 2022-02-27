
# Forming code jam teams though simulated annealing

`poetry run python control.py`

Needs heavy tuning. Most basic level is through the energy penalty values passed to `Cooler` in `control.py`, but likely needs some more in-depth changes in the `energy_levels` and `local_energy_audit` methods.