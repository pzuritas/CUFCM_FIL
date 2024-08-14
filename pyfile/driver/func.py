import configparser
import os
import util

class DRIVER:

    def __init__(self):
        self.globals_name = 'input/globals.ini'
        self.afix = ''
        self.category = 'elasticity-validation/'

        self.exe_name = 'cilia_1e-6_testing_build_a_beat'

        self.date = '20240814'

        self.dir = f"data/{self.category}{self.date}{self.afix}/"

        self.inputfile = f"input/states/temp/psi.dat"

        self.pars_list = {
                     "index": [],
                     "nswim": [],
                     "nseg": [],
                     "nfil": [],
                     "nblob": [],
                     "ar": [],
                     "spring_factor": [],
                     "force_mag": [],
                     "seg_sep": [],
                     "period": [],
                     "sim_length": [],
                     "nx": [],
                     "ny": [],
                     "nz": [],
                     "boxsize": [],
                     "fil_spacing": [],
                     "blob_spacing": [],
                     "fil_x_dim": [],
                     "blob_x_dim": [],
                     "hex_num": [],
                     "reverse_fil_direction_ratio": []}

        self.sweep_shape = (1, 1, 1, 1)

        self.num_sim = 0

        self.current_thread = 0
        self.num_thread = 1
        self.cuda_device = 0
    
    def update_date(self, date):
        self.date = date
        self.dir = f"data/{self.category}{self.date}{self.afix}/"

    def create_ini(self):
        ini = configparser.ConfigParser()
        ini.add_section('Parameters')
        ini.add_section('Filenames')
        ini.add_section('Box')
        ini.add_section('Hex')
        ini.add_section('Concentric')
        ini.add_section('Seeding_util')
        with open(self.globals_name, 'w') as configfile:
            ini.write(configfile, space_around_delimiters=False)
        
    def write_ini(self, section, variable, value):
        ini = configparser.ConfigParser()
        ini.read(self.globals_name)

        ini.set(section, variable, f'{value}')

        # Save the changes back to the file
        with open(self.globals_name, 'w') as configfile:
            ini.write(configfile, space_around_delimiters=False)

    def create_rules(self):
        # Define the rule of sweeping simulations
        index = 0
        for i in range(self.sweep_shape[0]):
            for j in range(self.sweep_shape[1]):
                for k in range(self.sweep_shape[2]):
                    for l in range(self.sweep_shape[3]):

                        seg_sep = 2.6
                        nseg = 11
                        force_mag = 1

                        # # planar triangle
                        nfil = int(1*(i+1))
                        nblob = int(0*(i+1))
                        ar = round(1, 2)
                        period = 1
                        spring_factor = 1e-3 # k_tidle
                        nx=256
                        ny=256
                        nz=32
                        boxsize=8000
                        fil_spacing=80.0
                        blob_spacing=8.0
                        fil_x_dim=16*(i+1)
                        blob_x_dim=160*(i+1)
                        hex_num=2
                        reverse_fil_direction_ratio=0.0
                        sim_length = 20.0

                        if(self.exe_name == 'cilia_ref'):
                            nfil = 1
                            nblob = 0
                            
                        self.pars_list["index"].append(index)
                        self.pars_list["nswim"].append(1)
                        self.pars_list["nseg"].append(nseg)
                        self.pars_list["nfil"].append(nfil)
                        self.pars_list["nblob"].append(nblob)
                        self.pars_list["ar"].append(ar)
                        self.pars_list["spring_factor"].append(spring_factor)
                        self.pars_list["force_mag"].append(force_mag)
                        self.pars_list["seg_sep"].append(seg_sep)
                        self.pars_list["period"].append(period)
                        self.pars_list["sim_length"].append(sim_length)
                        self.pars_list["nx"].append(nx)
                        self.pars_list["ny"].append(ny)
                        self.pars_list["nz"].append(nz)
                        self.pars_list["boxsize"].append(boxsize)
                        self.pars_list["fil_spacing"].append(fil_spacing)
                        self.pars_list["blob_spacing"].append(blob_spacing)
                        self.pars_list["fil_x_dim"].append(fil_x_dim)
                        self.pars_list["blob_x_dim"].append(blob_x_dim)
                        self.pars_list["hex_num"].append(hex_num)
                        self.pars_list["reverse_fil_direction_ratio"].append(reverse_fil_direction_ratio)

                        index += 1
        # Write rules to sim list file
        self.write_rules()

    def delete_files(self):
        util.delete_files_in_directory(self.dir)

    def view_files(self):
        util.view_files_in_directory(self.dir)
        print(f"\033[32m{self.dir}\033[m")
        print(f"\033[34m{self.exe_name}\033[m")

    def write_rules(self):
        os.system(f'mkdir -p {self.dir}')
        sim = configparser.ConfigParser()
        sim.add_section('Parameter list')
        for key, value in self.pars_list.items():
            sim['Parameter list'][key] = ', '.join(map(str, value))
        with open(self.dir+"rules.ini", 'w') as configfile:
            sim.write(configfile, space_around_delimiters=False)

    def read_rules(self):
        sim = configparser.ConfigParser()
        try:
            sim.read(self.dir+"rules.ini")
            for key, value in self.pars_list.items():
                if(key in sim["Parameter list"]):
                    self.pars_list[key] = [float(x) for x in sim["Parameter list"][key].split(', ')][0::1]
            self.num_sim = len(self.pars_list["nfil"])            
        except:
            print("WARNING: " + self.dir + "rules.ini not found.")

    def run(self):
        self.create_ini()
        self.write_ini("Filenames", "simulation_dir", self.dir)

        # Read rules from the sim list file
        self.read_rules()

        thread_list = util.even_list_index(self.num_sim, self.num_thread)
        sim_index_start = thread_list[self.current_thread]
        sim_index_end = thread_list[self.current_thread+1]

        print(f"Partitioning {self.num_sim} into {self.num_thread} threads\n" +\
              f"Partition index: {self.current_thread} / {self.num_thread-1} \n" + \
              f"[{sim_index_start} - {sim_index_end}] / {thread_list}\n" +\
              f"on GPU: {self.cuda_device}")
        
        # Iterate through the sim list and write to .ini file and execute
        for i in range(sim_index_start, sim_index_end):
            
            for key, value in self.pars_list.items():
                self.write_ini("Parameters", key, float(self.pars_list[key][i]))
            self.simName = f"ciliate_{self.pars_list['nfil'][i]:.0f}fil_{self.pars_list['nblob'][i]:.0f}blob_{self.pars_list['ar'][i]:.2f}R_{self.pars_list['spring_factor'][i]:.4f}torsion"
            self.write_ini("Filenames", "simulation_file", self.simName)
            self.write_ini("Filenames", "simulation_dir", self.dir)
            self.write_ini("Filenames", "simulation_icstate_name", f"{self.dir}psi{i}.dat")
            self.write_ini("Filenames", "cufcm_config_file_name", f"input/simulation_info_cilia")

            # command = f"export OPENBLAS_NUM_THREADS=1; \
            #             export CUDA_VISIBLE_DEVICES={self.cuda_device}; \
            #             ./bin/{self.exe_name} > terminal_outputs/output_{self.date}_{self.pars_list['nfil'][i]:.0f}fil_{i}.out"

            command = f"export OPENBLAS_NUM_THREADS=1; \
                        export CUDA_VISIBLE_DEVICES={self.cuda_device}; \
                        ./bin/{self.exe_name} > temp.out"
            
            # on ic hpc
            # command = f"export OPENBLAS_NUM_THREADS=1; \
            #             ./bin/{self.exe_name}"


            os.system(command)
