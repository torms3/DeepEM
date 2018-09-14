from __future__ import print_function
import numpy as np

import torch
from torch import nn
from torch.nn import functional as F

from deepem.utils import py_utils


def get_pair_first(arr, edge):
    shape = arr.size()[-3:]
    edge = np.array(edge)
    os1 = np.maximum(edge, 0)
    os2 = np.maximum(-edge, 0)
    ret = arr[..., os1[0]:shape[0]-os2[0],
                   os1[1]:shape[1]-os2[1],
                   os1[2]:shape[2]-os2[2]]
    return ret


def get_pair(arr, edge):
    shape = arr.size()[-3:]
    edge = np.array(edge)
    os1 = np.maximum(edge, 0)
    os2 = np.maximum(-edge, 0)
    arr1 = arr[..., os1[0]:shape[0]-os2[0],
                    os1[1]:shape[1]-os2[1],
                    os1[2]:shape[2]-os2[2]]
    arr2 = arr[..., os2[0]:shape[0]-os1[0],
                    os2[1]:shape[1]-os1[1],
                    os2[2]:shape[2]-os1[2]]
    return arr1, arr2


def get_pair_first2(arr, edge):
    # Margin correction (only works for (1,1,1))
    edge = np.array(list(map(lambda x: x - np.sign(x), edge)))
    os1 = np.maximum(edge, 0)
    os2 = np.maximum(-edge, 0)
    shape = arr.size()[-3:]
    ret = arr[..., os1[0]:shape[0]-os2[0],
                   os1[1]:shape[1]-os2[1],
                   os1[2]:shape[2]-os2[2]]
    return ret


def get_pair2(arr, edge):
    edge = np.array(edge)
    os1 = np.maximum(edge, 0)
    os2 = np.maximum(-edge, 0)

    shape = arr.size()[-3:]
    arr1 = arr[..., os1[0]:shape[0]-os2[0],
                    os1[1]:shape[1]-os2[1],
                    os1[2]:shape[2]-os2[2]]
    arr2 = arr[..., os2[0]:shape[0]-os1[0],
                    os2[1]:shape[1]-os1[1],
                    os2[2]:shape[2]-os1[2]]

    # Margin correction (only works for (1,1,1))
    m1 = list(map(lambda x: 0 if x > 0 else 1, edge))
    m2 = list(map(lambda x: 0 if x < 0 else 1, edge))

    shape = arr1.size()[-3:]
    arr1 = arr1[..., m1[0]:shape[0]-m2[0],
                     m1[1]:shape[1]-m2[1],
                     m1[2]:shape[2]-m2[2]]
    arr2 = arr2[..., m1[0]:shape[0]-m2[0],
                     m1[1]:shape[1]-m2[1],
                     m1[2]:shape[2]-m2[2]]

    return arr1, arr2


def affinity(v1, v2, dim=-4, keepdims=True, mean_loss=False, gamma=3.0):
    if mean_loss:
        norm = torch.norm(v1 - v2, p=1, dim=dim, keepdim=keepdims)
        margin = (gamma - norm) / gamma
        zero = torch.zeros(1).type(v1.type())
        return torch.max(zero, margin)**2
    else:
        d2 = torch.sum((v1 - v2)**2, dim=dim, keepdim=keepdims)
        return torch.exp(-d2)


def vec2aff(v, aff=(1,1,1), mean_loss=False, gamma=3.0):
    assert(v.ndimension() >= 4)
    x,y,z = aff
    xaff = affinity(*(get_pair(v, (0,0,x))), mean_loss=mean_loss, gamma=gamma)
    yaff = affinity(*(get_pair(v, (0,y,0))), mean_loss=mean_loss, gamma=gamma)
    zaff = affinity(*(get_pair(v, (z,0,0))), mean_loss=mean_loss, gamma=gamma)
    xaff = F.pad(xaff, (x,0))
    yaff = F.pad(yaff, (0,0,y,0))
    zzff = F.pad(zaff, (0,0,0,0,z,0))
    assert xaff.size() == yaff.size() == zaff.size()
    return torch.cat((xaff,yaff,zaff), dim=-4)


def vec2pca(v):
    assert v.ndimension() == 5
    vec = v.cpu().numpy()
    pca = py_utils.fit_pca(vec)
    vec = py_utils.pca_scale_vec(vec, pca)
    return torch.from_numpy(vec)
