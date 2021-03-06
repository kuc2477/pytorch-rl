"""
Class for a generic trainer used for training all the different generative models
"""
from models import infogan
from models.attention import *
from torch.utils.data import Dataset
import os
from skimage import io, transform
from torchvision import transforms
from Utils import tensorboard_writer
import torch.nn.functional as F

USE_CUDA = torch.cuda.is_available()


class StatesDataset(Dataset):
    """

    Dataset consisting of the frames of the Atari Game-
    Montezuma Revenge

    """

    def __init__(self, root_dir, transform=None):
        self.root_dir = root_dir
        self.transform = transform
        self.images = []
        self.list_files()

    def __len__(self):
        return len(self.images)

    def list_files(self):
        for m in os.listdir(self.root_dir):
            if m.endswith('.jpg'):
                self.images.append(m)

    def __getitem__(self, idx):
        m = self.images[idx]
        image = io.imread(os.path.join( self.root_dir, m))
        sample = {'image': image}

        if self.transform:
            sample = self.transform(sample)

        return sample

# Transformations
class Rescale(object):
    """Rescale the image in a sample to a given size.

    Args:
        output_size (tuple or int): Desired output size. If tuple, output is
            matched to output_size. If int, smaller of image edges is matched
            to output_size keeping aspect ratio the same.
    """

    def __init__(self, output_size):
        assert isinstance(output_size, (int, tuple))
        self.output_size = output_size

    def __call__(self, sample):
        image = sample['image']

        h, w = image.shape[:2]
        if isinstance(self.output_size, int):
            if h > w:
                new_h, new_w = self.output_size, self.output_size
            else:
                new_h, new_w = self.output_size, self.output_size * w / h
        else:
            new_h, new_w = self.output_size

        new_h, new_w = int(new_h), int(new_w)

        img = transform.resize(image, (new_h, new_w))

        return {'image': img}


class ToTensor(object):
    """Convert ndarrays in sample to Tensors."""


    def __call__(self, sample):
        image = sample['image']

        # swap color axis because
        # numpy image: H x W x C
        # torch image: C X H X W
        image = image.transpose((2, 0, 1))
        image = torch.FloatTensor(torch.from_numpy(image).float())
        return {'image': image}


if __name__ == '__main__':

    image_size = 128
    height_img = 128
    width_img = 128
    seed = 100
    input_images = 'montezuma_resources'

    dataset = StatesDataset(root_dir=input_images, transform=
        transforms.Compose([Rescale(image_size),ToTensor()]))
    generator = infogan.Generator(conv_layers=32, conv_kernel_size=2, latent_space_dimension=128,
                                   height=height_img, width=width_img, hidden_dim=128, input_channels=3)
    discriminator = infogan.Discriminator_recognizer(input_channels=3, conv_layers=32, conv_kernel_size=3, pool_kernel_size=2,
                                           hidden=64, height=height_img, width=width_img, cat_dim=10, cont_dim=2)

    if USE_CUDA:
        generator = generator.cuda()
        discriminator = discriminator.cuda()

    # Tensorboard writer for visualizing the training curves
    tb_writer = tensorboard_writer.TensorboardWriter()

    infogan_model = infogan.InfoGAN(generator=generator, discriminator=discriminator,
                                    dataset=dataset, batch_size=16, generator_lr=1e-4,
                                    discriminator_lr=4e-4, num_epochs=500, random_seed=seed,
                                    shuffle=True, tensorboard_summary_writer=tensorboard_writer,
                                    use_cuda=USE_CUDA, output_folder='infogan/inference/')
    infogan_model.train()



