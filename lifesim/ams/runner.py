import numpy as np
import os

# LIFEsim changes the working directory, so we must switch back to the original folder.
working_directory = os.getcwd()
import lifesim
from lifesim import TradeSpaceExplorer
from lifesim import ErrorBudget
from lifesim  import AgnosticMissionSimulator
os.chdir(working_directory)

if __name__ == '__main__':

    pth = input('>> Enter catalog [hi/lo]: ')

    cat_pth = f"../catalogs/catalog_hab2{pth}.txt"

    pth = cat_pth.split('.')[0]

    # create bus
    bus = lifesim.Bus()

    # setting the options
    bus.data.options.set_scenario('baseline')

    #bus.build_from_config(filename='settings.yaml')

    # ---------- Loading the Catalog ----------

    bus.data.catalog_from_ppop(input_path=cat_pth)
    # speed up calculation

    bus.data.options.set_manual(n_cpu=8, spec_res=20.0, image_size=160)

    # ---------- Creating the Instrument ----------

    # create modules and add to bus
    instrument = lifesim.Instrument(name='inst')
    bus.add_module(instrument)

    transm = lifesim.TransmissionMap(name='transm')
    bus.add_module(transm)

    exo = lifesim.PhotonNoiseExozodi(name='exo')
    bus.add_module(exo)
    local = lifesim.PhotonNoiseLocalzodi(name='local')
    bus.add_module(local)
    star = lifesim.PhotonNoiseStar(name='star')
    bus.add_module(star)

    # connect all modules
    bus.connect(('inst', 'transm'))
    bus.connect(('inst', 'exo'))
    bus.connect(('inst', 'local'))
    bus.connect(('inst', 'star'))
    bus.connect(('star', 'transm'))


    instrument.apply_options()

    instrument.get_snr()

    print('meep')

    opt = lifesim.Optimizer(name='opt')
    bus.add_module(opt)
    ahgs = lifesim.AhgsModule(name='ahgs')
    bus.add_module(ahgs)

    bus.connect(('transm', 'opt'))
    bus.connect(('inst', 'opt'))
    bus.connect(('opt', 'ahgs'))

    m = (1950 - 0)/(bus.data.options.array['wl_max']*1e-6 - bus.data.options.array['wl_min']*1e-6)
    n = 1950 - bus.data.options.array['wl_max']*1e-6 * m

    widths = bus.data.inst['wl_bin_widths'] * 1e6

    budget = ErrorBudget(additive_factor=lambda args: (m*args[3] + n) * widths)

    # Plot-IDs:
    # Hi: 9
    # Lo: 5
    ams = AgnosticMissionSimulator(2, 7, 65 / 360 * 2*np.pi, 0.8, 12*60*60,
                                   verbose=False, plot_id=None)

    tse = TradeSpaceExplorer(ams, opt, instrument)

    tse.plot_cutoff_for_slewtime(6)
    exit()

    mtime = float(input('>> Enter mission time in years: '))

    #plots.plot_cutoff_for_slewtime(instrument, opt, ams, mtime)
    #plots.plot_linear_regression_additive(instrument, opt, ams)

    #plots.plot_linear_regression_additive(instrument, opt, ams)




    exit()
    def gradient_setter_function(ams, budget, mode):
        if mode == 'short-long':
            m = (budget - 0) / (bus.data.options.array['wl_max'] * 1e-6 - bus.data.options.array['wl_min'] * 1e-6)
            n = budget - bus.data.options.array['wl_max'] * 1e-6 * m
        elif mode == 'long-short':
            m = (0 - budget) / (bus.data.options.array['wl_max'] * 1e-6 - bus.data.options.array['wl_min'] * 1e-6)
            n = 0 - bus.data.options.array['wl_max'] * 1e-6 * m
        else:
            raise ValueError(f'Unknown mode: {mode}')
        ams.get_leakage_budget().update_factors(additive_factor=lambda args: (m * args[3] + n) * widths)

    print('no gradient', plots.locate_mission_cutoff(instrument, opt, ams, mtime, upper_start=5000))

    print('long-short gradient', plots.locate_mission_cutoff(instrument, opt, ams, mtime, upper_start=5000,
                                      setter_func=lambda ams, bud:
                                      gradient_setter_function(ams, bud, 'long-short')))

    print('short-long gradient', plots.locate_mission_cutoff(instrument, opt, ams, mtime, upper_start=5000,
                                      setter_func=lambda ams, bud:
                                      gradient_setter_function(ams, bud, 'short-long')))

