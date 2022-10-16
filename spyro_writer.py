class SpyroData:
    def __init__(self, file_name, folder_location):
        """Constructor

        Parameters
        ----------
        file_name :
            string with the simulation file name
        folder_location :
            string with the folder file name

        Objects
        -------
        feed_comp_wt :
            DataFrame which is constructed by the transform_naphtha_feed
            function
        """

        self.file_name = file_name
        self.folder_location = folder_location
        self.feed_composition = FeedComposition()

    def get_file_name(self):
        return self.file_name

    def get_spyro_exe_location(self):
        return self.spyro_exe_location

    def get_folder_location(self):
        return self.folder_location

    def set_feed_composition(self, feed_pitagor, feed_converter):
        """set_feed_composition.

        Parameters
        ----------
        feed_composition :
            DataFrame/Series including Spyro names as index and weight percent
            Created via the transform_naphtha_feed function
        """
        self.feed_composition.set_feed_composition(
            feed_pitagor, feed_converter
        )

    def set_file_name(self, file_name):
        self.file_name = file_name

    def set_spyro_exe_location(self, spyro_exe_location):
        self.spyro_exe_location = spyro_exe_location

    def write_spyro(self):
        # copy the example file in the folder location with new folder and name
        # find the keywords to change with the data in self
        # close the newly file copied from the example file
        pass

    def create_naphtha_line(self, ecf_dat):
        """create_naphtha_line.

        ecf_dat :
            string indicating either ecf or dat to indicate in which format the
            naphtha feed line should be printed

        Returns
        -------
        naphtha_line_string
            String in the SPYRO format, ecf or dat
        """

        print("writing naphtha input line.")
        self.naphtha_line_string = ""
        feed_comp_wt_dct = self.feed_composition.get_feed_comp().to_dict()
        if ecf_dat == "dat":
            # create .dat file input
            self.naphtha_line_string += "KEYW=&NAME\n"
            self.naphtha_line_string += (
                "   "
                + ", ".join(
                    "{}={:}".format(key, value,)
                    for key, value in feed_comp_wt_dct.items()
                )
                + ", END"
            )
        elif ecf_dat == "ecf":
            # create .ecf file input
            self.naphtha_line_string += "[NAME]\n"
            self.naphtha_line_string += " ".join(
                "{} {}".format(key, value)
                for key, value in feed_comp_wt_dct.items()
            )

        return self.naphtha_line_string


class FeedComposition:
    def __init__(self):
        """Constructor

        Parameters
        ----------
        feed_pitagor :
            naphtha dataframe read from Pitagor excel output
        feed_converter :
            naphtha converter dataframe file
            to transform lab data name to SPYRO names

        Objects
        -------
        feed_comp_wt :
            DataFrame which is constructed by the transform_naphtha_feed
            function
        """
        import pandas as pd

        self.translator_df = pd.DataFrame()
        self.feed_composition_df = pd.DataFrame()
        # pitagor output wt components incl measured PIONA components
        self.feed_comp_wt_sub = pd.DataFrame()
        # Individual components only
        # Default feed composition is 100 % ethane
        self.feed_comp_wt = pd.DataFrame({"C2H6": [100]})
        # Sum of weight based components
        self.total_sum = 0

        # PIONA composition
        self.df_piona = pd.DataFrame()
        self.piona_total_error = 0

    def get_feed_comp(self, wt_mol="wt"):
        if wt_mol == "wt":
            return self.feed_comp_wt
        else:
            pass

    def get_feed_translator(self):
        return self.translator_df

    def get_df_piona(self):
        return self.df_piona

    def get_piona_error(self):
        return self.piona_total_error

    def set_feed_composition(self, feed_pitagor, feed_converter):
        """
        Parameters
        ----------
        feed_pitagor :
            naphtha dataframe read from Pitagor excel output
        feed_converter :
            naphtha converter dataframe file
            to transform lab data name to SPYRO names
        """
        self.translator_df = feed_converter
        self.feed_composition_df = feed_pitagor

    def piona_processor(self):
        naphtha_piona_converter = self.translator_df.set_index("Spyro_name")

        # Remove duplicate indices and take only the PIONA column
        naphtha_piona_converter = naphtha_piona_converter.loc[
            ~naphtha_piona_converter.index.duplicated(keep="first")
        ]["PIONA"]
        # Add PIONA to the naphtha composition
        feed_comp_wt_piona_test = (
            pd.concat([self.feed_comp_wt, naphtha_piona_converter], axis=1,)
            .reindex(self.feed_comp_wt.index)
            .fillna(0)
        )

        # Sum PIONA components
        piona_comp = feed_comp_wt_piona_test.groupby("PIONA").sum()
        # Analysed PIONA components
        piona_feed = (
            self.feed_comp_wt_sub.set_index("DESCRIPTION COMPOSANT")["VALEUR"]
            .astype("float64")
            .fillna(0)
        )

        dct_piona_list = {
            "A": "Totaal aromaten(gew)",
            "I": "Totaal iso-paraffinen(gew)",
            "P": "Totaal n-paraffinen(gew)",
            "O": "Totaal olefinen(gew)",
        }
        # The total amount of naphthenes is not given in the lab data so a
        # subtraction of the total is used.
        piona_feed["Totaal naftenen(gew)"] = (
            100 - piona_feed[dct_piona_list.values()].sum()
        )
        dct_piona_list["N"] = "Totaal naftenen(gew)"

        # Combine the calculated and analysed data in a DataFrame (table)
        dct_piona = {}
        for key, value in dct_piona_list.items():
            dct_piona[value] = [
                round(piona_comp.loc[key, "VALEUR"], ndigits=2,),
                round(piona_feed.loc[value], ndigits=2),
            ]
        self.df_piona = pd.DataFrame(dct_piona,).transpose()
        self.df_piona.columns = ["Calculated", "Analysed"]

        # Calculate the difference between analysed and calculated.
        self.df_piona["difference"] = abs(
            self.df_piona["Calculated"] - self.df_piona["Analysed"]
        )
        self.piona_total_error = self.df_piona["difference"].sum()
        print(self.df_piona)
        if self.piona_total_error > 2.0:
            print(
                "[ERROR]\ncalculated PIONA composition does not match the \
                analyzed composition."
            )
        elif self.piona_total_error > 1.0:
            print(
                "[WARNING]\ncalculated PIONA composition is slightly \
                        different to the analyzed composition."
            )
        else:
            pass
        print(
            "The total PIONA error is {:.2f} %".format(self.piona_total_error)
        )

    def transform_naphtha_feed(
        self,
        # naphtha_dataframe,
        # naphtha_converter,
        log=False,
        normalize=True,
        check_piona=True,
    ):
        """transform_naphtha_feed.

        Parameters
        ----------
        log :
            boolean for printing log output
        normalize :
            boolean to normalize the naphtha feed data or not
        check_piona :
            boolean to check if the piona composition matches the lab analysis
        """
        import pandas as pd

        if log:
            print("transformation started.")
        # Select all rows with weight based value components
        mask_wt = self.feed_composition_df["UNITÉ DE MESURE"] == "PCT_GEW"
        self.feed_comp_wt_sub = self.feed_composition_df[mask_wt]

        # Change the naphtha file name to Spyro specific component name
        self.feed_comp_wt = self.feed_comp_wt_sub.replace(
            naphtha_converter["Spyro_name"].to_dict()
        ).set_index("DESCRIPTION COMPOSANT")["VALEUR"]
        self.feed_comp_wt = self.feed_comp_wt.replace(
            to_replace="<0.50", value=0
        )
        self.feed_comp_wt = self.feed_comp_wt[
            self.feed_comp_wt.index.notnull()
        ]
        self.feed_comp_wt = self.feed_comp_wt.astype("float64")

        self.total_sum = self.feed_comp_wt.sum()
        if abs(self.total_sum - 100) >= 2:
            print(
                "[ERROR]\nTotal sum of naphtha feed from lab analysis \
                is not 100% \
                ({}) perhaps components are missing in the converter \
                file".format(
                    self.total_sum
                )
            )
        if abs(self.total_sum - 100) >= 1:
            print(
                "[WARNING]\nTotal sum of naphtha feed from lab analysis \
                is not 100% \
                ({}) perhaps components are missing in the converter \
                file".format(
                    self.total_sum
                )
            )

        # Normalize to 100%
        if normalize:
            self.feed_comp_wt = self.feed_comp_wt / self.total_sum * 100
            if log:
                print("feed normalized")

        # Check if the piona composition matches the lab results
        if check_piona:
            if log:
                print("Start PIONA comparison.")
            self.piona_processor()

        if log:
            print(self.feed_comp_wt)

        return self.get_feed_comp()


class EffluentComposition:
    def __init__(self):


def read_naphtha_spyro_converter(file_name, log=False):
    """read_naphtha_spyro_converter.

    Parameters
    ----------
    file_name :
        string which indicates the excel file name for the converter file
    log :
        boolean for printing log output

    Returns
    -------
    nafta_converter
        DataFrame with lab names and SPYRO names
    """
    import os
    import pickle

    import pandas as pd

    # Store the spyro converter file in a python pickle format for faster
    # reading
    processing_dir = ".\\processing_files"
    converter_file_str_name = "converter_file.pkl"
    converter_file_location = processing_dir + "\\" + converter_file_str_name
    if not os.path.isdir(processing_dir):
        os.mkdir(processing_dir)
    else:
        if os.path.isfile(converter_file_location):
            pickle.load(open(converter_file_location, "rb"))

    if log:
        print("read converter")
    # TODO Add checks if the file exists and has the correct attributes
    nafta_converter = pd.read_excel(
        file_name, sheet_name="Detailed_comp"
    ).set_index("Lab_name")
    if log:
        print(nafta_converter)

    pickle.dump(nafta_converter, open(converter_file_location, "wb"))
    print("Converter file saved.")

    return nafta_converter


if __name__ == "__main__":
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd

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
        spyro_data[i] = SpyroData(feed_name, ".")

        feed_comp_test = feed_comp[feed_name]
        spyro_data[i].set_feed_composition(
            feed_pitagor=feed_comp_test, feed_converter=naphtha_converter
        )
        spyro_data[i].feed_composition.transform_naphtha_feed()

        print(spyro_data[i].create_naphtha_line(ecf_dat="dat"))
