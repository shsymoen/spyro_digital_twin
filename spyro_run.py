def main():
    """main runner and testing for spyro."""
    import os

    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd

    from spyro_framework.spyro import (
        EffluentComposition,
        FeedComposition,
        SpyroData,
        read_naphtha_spyro_converter,
    )

    feed_comp = pd.read_excel(
        "Samples Naphtha2.xlsx",
        skiprows=8,
        sheet_name=None,
        parse_dates=True,
        na_values=["<0.50"],
    )

    file_name = "naphtha_converter_TRAlab_Spyro.xlsx"
    naphtha_converter = read_naphtha_spyro_converter(file_name)

    spyro_data = {}
    for i, feed_name in enumerate(feed_comp):
        spyro_data[i] = SpyroData(feed_name, os.getcwd())

        feed_comp_test = feed_comp[feed_name]
        spyro_data[i].set_feed_composition(
            feed_pitagor=feed_comp_test, feed_converter=naphtha_converter
        )
        spyro_data[i].feed_composition.transform_naphtha_feed()
        spyro_data[i].write_spyro()

    #     for spyro_simulation_nr in spyro_data:
    #         spyro_data[spyro_simulation_nr].run_spyro()
    for spyro_simulation_nr in spyro_data:
        spyro_sim = spyro_data[spyro_simulation_nr]
        print(
            "reading effluent data for simulation                {}".format(
                spyro_sim.get_file_name()
            )
        )
        spyro_sim.effluent_composition.read_effluent(
            spyro_sim.get_folder_location(), spyro_sim.get_file_name()
        )

    test = spyro_data[0].effluent_composition.effluent["wt"]
    print(test)


if __name__ == "__main__":
    main()
