import os

import numpy as np

# LIFESim changes the working directory, so we must switch back to the original folder.
working_directory = os.getcwd()
import lifesim
os.chdir(working_directory)

def create_data(model):
    # Generates data and returns the bus.

    pth = 'model' if model else 'conventional'

    # create bus
    bus = lifesim.Bus()

    if os.path.isfile(pth + '.yaml'):
        print('>> Files found, no calculation necessary. Returning data for analysis...')
        bus.build_from_config(pth + '.yaml')
        bus.data.import_catalog(input_path=pth + '_catalog.hdf5')
        return bus

    print('Files not found. Calculating data from scratch...')

    # setting the options
    bus.data.options.set_scenario('baseline')

    if model:
        bus.data.options.set_manual(stellar_leakage_decoupling=True)

    # ---------- Loading the Catalog ----------

    bus.data.catalog_from_ppop(input_path='small_catalog_lifesim_tutorial.txt', )
    # speed up calculation

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

    bus.data.options.set_manual(limit_mode='experiments',
                                experiments={'Experiment_1': {'radius_p_min': 0.5,
                                                              'radius_p_max': 1.5,
                                                              'temp_s_min': 4370.,
                                                              'temp_s_max': 7310.,
                                                              'in_HZ': True,
                                                              'sample_size': 30},
                                             'Experiment_2': {'radius_p_min': 0.5,
                                                              'radius_p_max': 1.5,
                                                              'temp_s_min': 3320.,
                                                              'temp_s_max': 4370.,
                                                              'in_HZ': True,
                                                              'sample_size': 15},
                                             },
                                output_path='',
                                output_filename=pth
                                )
    # optimizing the result
    opt = lifesim.Optimizer(name='opt')
    bus.add_module(opt)
    ahgs = lifesim.AhgsModule(name='ahgs')
    bus.add_module(ahgs)

    bus.connect(('transm', 'opt'))
    bus.connect(('inst', 'opt'))
    bus.connect(('opt', 'ahgs'))

    opt.ahgs()

    bus.save()

    return bus

if __name__ == '__main__':

    # Create bus for analysis
    bus_model = create_data(model=True)
    bus_conv = create_data(model=False)

    mask_model = np.logical_and(bus_model.data.catalog.detected, bus_model.data.catalog.habitable)
    mask_conv = np.logical_and(bus_conv.data.catalog.detected, bus_conv.data.catalog.habitable)

    yield_model = mask_model.sum() / 50
    yield_conv = mask_conv.sum() / 50

    # RESULTS
    print('\n ---   F U L L   D A T A   V A L I D A T I O N   ---\n')

    print(f'>> The model yields {yield_model} detections per universe.')
    print(f'>> The conventional method yields {yield_conv} detections per universe.')
    print()

    if yield_model > yield_conv:
        print('>> The model yields more detections than the conventional method (model too optimistic).')
    else:
        print('>> The conventional method yields more detections than the model (model too pessimistic).')

    print(f'>> Total Deviation (Model / Conventional): {round((yield_model / yield_conv - 1) * 100, 2)}%')
