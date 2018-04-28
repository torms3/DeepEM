from __future__ import print_function
import imp

import torch
from torch.utils.data import DataLoader

from pytorch_connectome.data.dataloader import DataLoader
from pytorch_connectome.data.dataset import Dataset, worker_init_fn


class Data(object):
    def __init__(self, opt, phase, device=None):
        assert phase in ['train','eval']
        self.build(opt, phase, device)

    def __call__(self):
        sample = next(self.dataiter)
        for k in sample:
            sample[k].requires_grad_(self.requires_grad(k))
            sample[k] = sample[k].to(self.device)
            # TODO: Non-blocking data transfer?
        return sample

    def requires_grad(self, key):
        return self.is_train and (k in self.inputs)

    def build(self, opt, phase, device):
        # Data
        mod = imp.load_source('data', opt.data_pathname)
        data = mod.load_data(opt.data_dir)

        # Data augmentation
        mod = imp.load_source('augment', opt.augment_pathname)
        aug = mod.get_augmentation(phase)

        # Data sampler
        mod = imp.load_source('sampler', opt.sampler_pathname)
        spec = mod.get_spec(opt.in_spec, opt.out_spec)
        sampler = mod.Sampler(data, spec, aug)

        # Data loader
        size = (opt.max_iter - opt.chkpt_num) * opt.batch_size
        dataset = Dataset(sampler, size)
        dataloader = DataLoader(dataset,
                                batch_size=opt.batch_size,
                                num_workers=opt.num_workers,
                                pin_memory=True,
                                worker_init_fn=worker_init_fn)

        # Attributes
        self.dataiter = iter(dataloader)
        self.inputs = opt.in_spec.keys()
        self.is_train = (phase=='train')
        self.device = torch.device('cuda') if device is None else device