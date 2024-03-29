class SpyroData:
    def __init__(self, file_name, folder_location, base_folder="base"):
        """Constructor

        Parameters
        ----------
        file_name :
            string with the simulation file name
        folder_location :
            string with the folder file name
        base_folder :
            string with base folder and file name, default: base

        Objects
        -------
        feed_comp_wt :
            DataFrame which is constructed by the transform_naphtha_feed
            function
        """
        import os

        # File name of the spyro .dat file
        # The file name and the dedicated folder should have the same name
        self.file_name = file_name
        # The folder where the files are stored
        self.folder_location = folder_location
        # Class that has all information on the feed composition
        self.feed_composition = FeedComposition()
        # Class that has all information with regard to the converging criteria
        self.convergence = Convergence()
        # Class that has all information on the effluent composition
        self.effluent_composition = EffluentComposition()
        # Create the output container class for spyro
        self.general_spyro = SpyroGeneralOutput()
        # Create the output container class for firebox
        self.firebox = FireboxData()
        # String where the exe file of Spyro is located
        self.spyro_exe_location = r"C:\Program Files (x86)\Pyrotec\EFPS86"
        # Spyro exe name
        self.spyro_exe_name = r"EFPS68.exe"
        # Exact name for spyro execution
        self.spyro_exe_loc_name = os.path.join(
            self.spyro_exe_location, self.spyro_exe_name
        )
        # folder name that can be used to copy the .dat file as example
        self.base_folder = os.path.join(self.folder_location, "base")
        # specific folder where the file is stored. Same name as the .dat
        # file
        self.file_name_folder = os.path.join(
            self.folder_location, self.file_name
        )

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

    def change_feed_composition(self, spyro_input_string):
        """Change feed composition"""
        import re

        feed_replacement_string = self.create_naphtha_line()
        spyro_input_string = re.sub(
            "KEYW=&NAME\n[\s\S]*, END",
            feed_replacement_string,
            spyro_input_string,
        )
        return spyro_input_string

    def change_convergence_target(self, spyro_input_string):
        import re

        target = self.convergence.target
        target_value = self.convergence.target_value
        spyro_input_string = re.sub(
            "CONOP=[0-9]",
            "CONOP={}".format(target),
            spyro_input_string,
        )

        target_value_keyword = {
            1: "TEMPO",  # COT
            2: "CONVAL",  # C3/ethylene ratio
            3: "CONVAL",  # P/E ratio
            4: "CONVAL",  # M/P ratio
            5: "CONVAL",  # Decomposition key component
            6: "CONVAL",  # total absorbed heat duty
        }

        if self.convergence.target in [1]:
            spyro_input_string = re.sub(
                "{}=[^,]*".format(target_value_keyword[target]),
                "{}={}".format(target_value_keyword[target], target_value),
                spyro_input_string,
            )
        else:
            spyro_input_string = re.sub(
                "{}=[^,]*".format(target_value_keyword[target]),
                "{}={}".format(target_value_keyword[target], target_value),
                spyro_input_string,
            )

        return spyro_input_string

    def write_spyro(self):
        import os
        import re
        import shutil

        # Change to current working directory
        cwd = os.getcwd()

        # copy the example file in the folder location with new folder and name
        src = os.path.join(self.base_folder, "base.dat")
        src_pyro_ini = os.path.join(self.base_folder, "Pyrotec.ini")
        dst = os.path.join(
            self.file_name_folder, "{}.dat".format(self.get_file_name())
        )
        # Create destination folder
        if not os.path.exists(self.file_name_folder):
            os.mkdir(self.file_name_folder)
        shutil.copy2(src, dst)
        shutil.copy(src_pyro_ini, self.file_name_folder)
        os.chdir(self.file_name_folder)

        # find the keywords to change with the data in self
        file_to_change = open("{}.dat".format(self.get_file_name()), "r")
        f_str = file_to_change.read()
        # Modify feed composition part
        f_str = self.change_feed_composition(f_str)
        # Modify conversion target
        f_str = self.change_convergence_target(f_str)
        # Close the reading file
        file_to_change.close()

        # overwrite the base file with the new feed line
        file_changed = open("{}.dat".format(self.get_file_name()), "w")
        file_changed.write(f_str)
        # close the newly file copied from the example file
        file_changed.close()
        print(
            "spyro files created in folder: {}".format(self.file_name_folder)
        )

        os.chdir(cwd)

    def read_spyro_output(self):
        self.effluent_composition.read_effluent(self.get_file_name())

    def run_spyro(self, verbose=True):
        """run_spyro.
        Runs Spyro EFPS in the self.folder_location

        Parameters
        ----------
        verbose :
            boolean to indicate whether to print the spyro output and errors
            or not.
        """
        import os
        import subprocess

        cwd = os.getcwd()
        os.chdir(os.path.join(self.folder_location, self.file_name))
        process = subprocess.Popen(
            [self.spyro_exe_loc_name, self.file_name + ".dat"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            #     executable=True,
        )
        stdout, stderr = process.communicate()
        if verbose:
            print(stdout.decode())
            print(stderr.decode())
        os.chdir(cwd)

    def create_naphtha_line(self, ecf_dat="dat"):
        """create_naphtha_line.

        ecf_dat :
            string indicating either ecf or dat to indicate in which file
            format the naphtha feed line should be printed. Default (.dat)

        Returns
        -------
        naphtha_line_string
            String in the SPYRO format, ecf or dat
        """
        import textwrap

        print("writing naphtha input line.")
        self.naphtha_line_string = ""
        feed_comp_wt_dct = self.feed_composition.get_feed_comp().to_dict()
        if ecf_dat == "dat":
            # create .dat file input
            self.naphtha_line_string += "KEYW=&NAME\n"
            substring = ""
            substring2 = ", ".join(
                "{}={:05f}".format(
                    key,
                    value,
                )
                for key, value in feed_comp_wt_dct.items()
            )
            lines = textwrap.wrap(substring2, 72, break_long_words=False)
            for line in lines:
                substring += "    {}*\n".format(line)
            self.naphtha_line_string += substring[:-2]
            self.naphtha_line_string += ", END"

        elif ecf_dat == "ecf":
            # create .ecf file input
            self.naphtha_line_string += "[NAME]\n"
            self.naphtha_line_string += " ".join(
                "{} {}".format(key, value)
                for key, value in feed_comp_wt_dct.items()
            )

        return self.naphtha_line_string


class Convergence:
    def __init__(self):
        """Constructor

        Parameters
        ----------

        Objects
        -------
        """
        self.target = 5  # represent COT convergence criteria
        self.target_value = 1.2


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
        import pandas as pd

        naphtha_piona_converter = self.translator_df.set_index("Spyro_name")

        # Remove duplicate indices and take only the PIONA column
        naphtha_piona_converter = naphtha_piona_converter.loc[
            ~naphtha_piona_converter.index.duplicated(keep="first")
        ]["PIONA"]
        # Add PIONA to the naphtha composition
        feed_comp_wt_piona_test = (
            pd.concat(
                [self.feed_comp_wt, naphtha_piona_converter],
                axis=1,
            )
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
                round(
                    piona_comp.loc[key, "VALEUR"],
                    ndigits=2,
                ),
                round(piona_feed.loc[value], ndigits=2),
            ]
        self.df_piona = pd.DataFrame(
            dct_piona,
        ).transpose()
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
            self.translator_df["Spyro_name"].to_dict()
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
        self.effluent = {}
        effluent_list = [
            "wt",
            "vol",
            "RC4",
            "RC4-pygas",
            "Pygas",
            "H/C ratio",
            "MW",
            "misc",
        ]
        for effluent_sublist in effluent_list:
            self.effluent[effluent_sublist] = {}

    def read_effluent(self, folder_location, file_name, verbose=False):
        import os
        import re

        import pandas as pd

        effl_df = 0
        folder_file_name = os.path.join(
            os.path.join(folder_location, file_name),
            "{}.eof".format(file_name),
        )
        with open(folder_file_name, "r") as output_file:
            f_str = output_file.read()
            effl_start_semi = f_str.rfind("[EFFLUENT]")
            effl_start = f_str.find(" ", effl_start_semi)
            effl_end = f_str.rfind("[EFFLUENT END]")
            effl_str = f_str[effl_start + 1 : effl_end]
            if verbose:
                print(effl_str)
            d = re.findall(r"([^\s]+)\s([0-9\.]+)", effl_str)
            effl_df = pd.DataFrame(d, columns=["Component", "Value"])
            effl_df = effl_df.set_index("Component")
            effl_df["Value"].astype("float64")

        for component in effl_df.index:
            if component[0] == "W":
                self.effluent["wt"][component[1:]] = effl_df.loc[
                    component, "Value"
                ]
            elif component[0] == "V":
                self.effluent["vol"][component[1:]] = effl_df.loc[
                    component, "Value"
                ]
            elif component[0] == "R":
                self.effluent["RC4-pygas"][component[1:]] = effl_df.loc[
                    component, "Value"
                ]
            elif component[0:2] == "HC":
                self.effluent["H/C ratio"][component[2:]] = effl_df.loc[
                    component, "Value"
                ]
            elif component[0:2] == "MW":
                self.effluent["MW"][component[2:]] = effl_df.loc[
                    component, "Value"
                ]
            else:
                self.effluent["misc"][component] = effl_df.loc[
                    component, "Value"
                ]

        for effluent_sub in self.effluent:
            self.effluent[effluent_sub] = pd.Series(
                self.effluent[effluent_sub]
            ).astype("float64")

        raw_c4_comps = [
            "C4H4",
            "BUTAD",
            "B1",
            "B2C",
            "B2T",
            "IB",
            "NBUTA",
            "IBUTA",
        ]
        self.effluent["RC4"] = self.effluent["RC4-pygas"].loc[raw_c4_comps]
        self.effluent["Pygas"] = self.effluent["RC4-pygas"].loc[
            ~self.effluent["RC4-pygas"].index.isin(raw_c4_comps)
        ]

        if verbose:
            print("Effluent succesfully read from Spyro output file")


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


class SpyroGeneralOutput:
    def __init__(self):
        import pandas as pd

        self.general = pd.DataFrame()

    def get_general(self):
        return self.general

    def read_general(self, folder_location, file_name, verbose=False):
        """
        Read the general output from a Spyro output file and return it as
        DataFrame.

        Parameters
        ----------
        folder_location : str
            The folder location where the Spyro output file is located.
        file_name : str
            The name of the Spyro output file.
        verbose : bool, optional
            Whether to print verbose output, by default False.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing the extracted data.

        Raises
        ------
        FileNotFoundError
            If the provided file_path does not exist.
        """
        import os

        import pandas as pd

        folder_file_name = os.path.join(
            os.path.join(folder_location, file_name),
            "{}.eof".format(file_name),
        )

        with open(folder_file_name, "r") as output_file:
            section = None
            for line in output_file:
                line = line.strip()
                if line.startswith("[SPYROGENERAL]"):
                    section = "SPYROGENERAL"
                elif line.startswith("[SPYROGENERAL END]"):
                    section = None
                elif section == "SPYROGENERAL":
                    splits = line.split()
                    parameters = splits[::2]
                    values = splits[1::2]

        df = pd.Series(values, index=parameters)
        df = df.astype("float64")

        # Rename the columns for df
        column_mapping = {
            "CIT": "Coil inlet temperature [°C]",
            "TXADIA": "Outlet temperature at measuring point [°C]",
            # "SURINS": "Transferline volume outlet temperature [°C]",
            "TMT": "Tube no. TMT",
            "MAXSKIN": "Maximum skin temperature [°C]",
            "COKRATE": "Coking rate at location of max TMT [mm/month]",
            "INLETP": "Coil inlet pressure [kgf/cm²]",
            "PRESSDR": "Pressure drop [kgf/cm²]",
            "OUTLETP": "Coil outlet pressure [kgf/cm²]",
            "MASSFL": "Feed flow per coil [kg/h]",
            "DSRATIO": "Steam dilution ratio [-]",
            "VELOLI": "Coil outlet linear velocity [m/s]",
            "VELOMA": "Coil outlet mass velocity [kg/m²s]",
            #         "": "Residence time up to coil outlet [s]",
            #         "": "Residence time including transfer line volume [s]",
            #         "": "Resulting convergence value [°C]",
            "TEMPWA": "Radiant wall temperature [°C]",
            "TEMPGA": "Radiant gas temperature [°C]",
            "TEMPCO": "Average correction of process temperature [°C]",
            "AVTMT": "Fourth power average tube skin temperature [°C]",
            "TOTDUT": "Total thermal duty transferred [kcal/h]",
            "HEATFA": "Average heat flux (clean int. surface) [kcal/m²h]",
            "COKVOL": "Total coil coke volume [dm³]",
            "VOLINS": "Total coil inside volume [dm³]",
            "SURINS": "Total coil inside surface [m²]",
            "SUROUT": "Total coil outside surface [m²]",
            "COILWE": "Total coil weight [kg]",
        }
        df = df.rename(index=column_mapping)

        if verbose:
            print("Spyro General Data and misc:")
            print(df)

        self.general = df


class FireboxData:
    def __init__(self):
        import pandas as pd

        self.firebox_present = False
        self.perform_section = False
        self.firebox_perf_summary = pd.DataFrame()

    def get_firebox_perf_summary(self):
        return self.firebox_perf_summary

    def read_firebox(self, folder_location, file_name, verbose=False):
        """
        Read the firebox output from a Spyro output file and return it as a
        DataFrame.

        Parameters
        ----------
        folder_location : str
            The folder location where the Spyro output file is located.
        file_name : str
            The name of the Spyro output file.
        verbose : bool, optional
            Whether to print verbose output, by default False.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing the extracted data.

        Raises
        ------
        FileNotFoundError
            If the provided file_path does not exist.
        """
        import os

        import pandas as pd

        folder_file_name = os.path.join(
            os.path.join(folder_location, file_name),
            "{}.eof".format(file_name),
        )

        with open(folder_file_name, "r") as output_file:
            data = []

            for line in output_file:
                line = line.strip()

                if line.startswith("[FIREBOX]"):
                    self.firebox_present = True

                if self.firebox_present and line.startswith("[PERFORM]"):
                    self.perform_section = True
                    continue

                if self.perform_section:
                    if line.startswith("["):
                        break
                    else:
                        data.append(line)

        if not self.firebox_present:
            print(
                "Warning: [FIREBOX] section not found in the file."
                "No data was parsed."
            )
            return None

        splits = data[0].split()
        parameters = splits[::2]
        values = splits[1::2]

        df = pd.Series(values, index=parameters)
        df = df.astype("float64")

        # Rename the columns for df
        column_mapping = {
            "EFFIFH": "Radiant box efficiency on fired heat [%]",
            "TOTFGF": "Total flue gas flow [kg/h]",
            "EFFIRH": "Radiant box efficiency on released heat [%]",
            "HENTFG": "Enthalpy of flue gas leaving radiant box [kcal/h]",
            "HEATF": "Fired heat based on LHV [kcal/h]",
            "HEATR": "Released heat based on LHV [kcal/h]",
            "HEATA": "Heat absorbed by tubes [kcal/h]",
            "HEATL": "Calculated heat losses in the radiant box [kcal/h]",
            "HEATO": "Heat leak through flue gas opening [kcal/h]",
            "HLEFT": "Bridge wall heat losses [kcal/h]",
            "BRDGTA": "Flue gas bridge temperature (average) [°C]",
            "BRDGTO": "Flue gas bridge temperature (overall) [°C]",
            "RBHEF": "Radiant box efficiency on fired heat [%]",
            "FLUETOW": "Total flue gas flow [kg/h]",
            "RBHER": "Radiant box efficiency on released heat [%]",
            "GASFSB": "Fuel gas flow [kg/h] (Side firing)",
            "GASFBB": "Fuel gas flow [kg/h] (Bottom firing)",
            "OILFSB": "Fuel oil flow [kg/h] (Side firing)",
            "OILFBB": "Fuel oil flow [kg/h] (Bottom firing)",
            "COMFSB": "Combustion air flow [kg/h] (Side firing)",
            "COMFBB": "Combustion air flow [kg/h] (Bottom firing)",
            "EXHFSB": "Gas turbine exhaust air flow [kg/h] (Side firing)",
            "EXHFBB": "Gas turbine exhaust air flow [kg/h] (Bottom firing)",
            "FLUECO2": "Carbon dioxide [mol%] (Flue gas)",
            "FLUEH2O": "Water (moisture) [mol%] (Flue gas)",
            "FLUEO2": "Oxygen [mol%] (Flue gas)",
            "FLUEN2": "Nitrogen [mol%] (Flue gas)",
            "FLUESO2": "Sulphur dioxide [mol%] (Flue gas)",
            "FLUEAR": "Argon [mol%] (Flue gas)",
            "AIRCO2": "Carbon dioxide [mol%] (Combustion Air)",
            "AIRH2O": "Water (moisture) [mol%] (Combustion Air)",
            "AIRO2": "Oxygen [mol%] (Combustion Air)",
            "AIRN2": "Nitrogen [mol%] (Combustion Air)",
            "AIRAR": "Argon [mol%] (Combustion Air)",
            "EXTCO2": "Carbon dioxide [mol%] (Exhaust)",
            "EXTH2O": "Water (moisture) [mol%] (Exhaust)",
            "EXTO2": "Oxygen [mol%] (Exhaust)",
            "EXTN2": "Nitrogen [mol%] (Exhaust)",
            "EXTAR": "Argon [mol%] (Exhaust)",
            "AIRAMW": "Molecular weight [kg/kmol] (Combustion Air)",
            "AIRTOM": "Total flow [kmol/h] (Combustion Air)",
            "AIRTOW": "Total flow [kg/h] (Combustion Air)",
            "EXTAMW": "Molecular weight [kg/kmol] (Exhaust)",
            "EXTTOM": "Total flow [kmol/h] (Exhaust)",
            "EXTTOW": "Total flow [kg/h] (Exhaust)",
            "FLUEAMW": "Molecular weight [kg/kmol] (Flue gas)",
            "FLUETOM": "Total flow [kmol/h] (Flue gas)",
            "BRDGLO": "Bridge wall heat losses [kcal/h]",
        }

        df = df.rename(index=column_mapping)

        if verbose:
            print("Firebox Data:")
            print(df)

        self.firebox_perf_summary = df
