from functools import reduce
import numpy as np

from keras.layers import Input, Conv2D, Dense, MaxPool2D, Flatten, Dropout
from keras.layers.advanced_activations import LeakyReLU, ReLU
from keras.layers.normalization import BatchNormalization
from keras.regularizers import l2
from keras.models import Model
from keras import backend as K
from PIL import Image


def compose(*funcs):
    if funcs:
        return reduce(lambda f, g: lambda *a, **kw: g(f(*a, **kw)), funcs)
    else:
        raise ValueError('Composition of empty sequence not supported.')


class Classifier(object):
    def __init__(self):
        classes_path = 'classifier_model_data/classes.txt'
        weights_path = 'classifier_model_data/weights.h5'

        with open(classes_path, 'r', encoding='utf-8') as f:
            self.classes = [i.strip() for i in f.readlines()]

        self.input_shape = (64, 64)
        self.model = self._net(in_shape=self.input_shape + (3, ), n_classes=len(self.classes))
        self.model.load_weights(weights_path)

        self.sess = K.get_session()

    @staticmethod
    def Conv2D_BN_Leaky(*args, **kwargs):
        conv_kwargs = {'use_bias': False, 'kernel_regularizer': l2(5e-3), 'padding': 'same'}
        conv_kwargs.update(kwargs)
        return compose(
            Conv2D(*args, **conv_kwargs),
            BatchNormalization(),
            LeakyReLU(alpha=0.1))

    def _net(self, in_shape=(64, 64, 3), n_classes=1000):
        in_layer = Input(in_shape)
        x = self.Conv2D_BN_Leaky(32, (3, 3))(in_layer)
        x = self.Conv2D_BN_Leaky(32, (3, 3))(x)
        x = MaxPool2D(2, 2, padding='same')(x)
        x = Dropout(rate=0.3)(x)

        x = self.Conv2D_BN_Leaky(64, (3, 3))(x)
        x = self.Conv2D_BN_Leaky(64, (3, 3))(x)
        x = MaxPool2D(2, 2, padding='same')(x)
        x = Dropout(rate=0.3)(x)

        x = self.Conv2D_BN_Leaky(128, (3, 3))(x)
        x = self.Conv2D_BN_Leaky(128, (3, 3))(x)
        x = self.Conv2D_BN_Leaky(128, (3, 3))(x)
        x = MaxPool2D(2, 2, padding='same')(x)
        x = Dropout(rate=0.3)(x)

        x = self.Conv2D_BN_Leaky(256, (3, 3))(x)
        x = self.Conv2D_BN_Leaky(256, (3, 3))(x)
        x = self.Conv2D_BN_Leaky(256, (3, 3))(x)
        x = MaxPool2D(2, 2, padding='same')(x)
        x = Dropout(rate=0.3)(x)

        x = Flatten()(x)
        preds = Dense(n_classes, activation='softmax')(x)
        model = Model(in_layer, preds)
        return model

    @staticmethod
    def get_image_data(image, input_shape):
        iw, ih = image.size
        h, w = input_shape
        scale = min(w / iw, h / ih)
        nw = int(iw * scale)
        nh = int(ih * scale)
        dx = (w - nw) // 2
        dy = (h - nh) // 2

        image = image.resize((nw, nh), Image.BICUBIC)
        new_image = Image.new('RGB', (w, h), (128, 128, 128))
        new_image.paste(image, (dx, dy))
        image_data = np.array(new_image) / 255.

        return np.array([image_data])

    def identify_image(self, image):
        image_data = self.get_image_data(image, self.input_shape)

        result = self.sess.run([self.model.output], feed_dict={self.model.input: image_data})
        result = self.classes[int(np.argmax(result[0]))]
        return result

    def close_session(self):
        self.sess.close()
