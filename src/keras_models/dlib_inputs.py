import os

import keras
from keras.layers import Input, Flatten, Dense, Conv2D, Dropout
from keras.models import Model
from nets.base import NeuralNet

from config import IMG_SIZE, MODEL_PATH, LEARNING_RATE, EPOCHS, BATCH_SIZE, DATA_SET_DIR, LOG_DIR, STEPS_PER_EPOCH
from util.BaseLogger import EmopyLogger


class DlibPointsInputNeuralNet(NeuralNet):
    """
    Neutral network whose inputs are dlib points, dlib points distances from centroid point
    and dlib points vector angle with respect to centroid vector.

    Parameters
    ----------
    input_shape : tuple
    
    """

    def __init__(self, input_shape, preprocessor=None, logger=None, train=True):
        """

        Args:
            input_shape:
            preprocessor:
            logger:
            train:
        """
        self.input_shape = input_shape
        self.models_local_folder = "dinn"
        self.logs_local_folder = self.models_local_folder
        self.preprocessor = preprocessor
        self.epochs = EPOCHS
        self.batch_size = BATCH_SIZE
        self.steps_per_epoch = STEPS_PER_EPOCH

        if not os.path.exists(os.path.join(LOG_DIR, self.logs_local_folder)):
            os.makedirs(os.path.join(LOG_DIR, self.logs_local_folder))
        if logger is None:
            self.logger = EmopyLogger([os.path.join(LOG_DIR, self.logs_local_folder, "nn.txt")])
        else:
            self.logger = logger
        self.feature_extractors = ["dlib"]
        self.number_of_class = self.preprocessor.classifier.get_num_class()
        if train:
            self.model = self.build()
        else:
            self.model = self.load_model(MODEL_PATH)

    def build(self):
        """
        Build neural network model
        
        Returns 
        -------
        keras.models.Model : 
            neural network model
        """

        dlib_points_input_layer = Input(shape=(1, 68, 2))
        dlib_points_layer = Conv2D(32, (1, 3), activation='relu', padding="same", kernel_initializer="glorot_normal")(
            dlib_points_input_layer)
        dlib_points_layer = Conv2D(64, (1, 3), activation="relu", padding="same", kernel_initializer="glorot_normal")(
            dlib_points_layer)
        # dlib_points_layer = Conv2D(128,(1, 3),activation = "relu",padding="same",kernel_initializer="glorot_normal")(dlib_points_layer)

        dlib_points_layer = Flatten()(dlib_points_layer)

        dlib_points_dist_input_layer = Input(shape=(1, 68, 1))
        dlib_points_dist_layer = Conv2D(32, (1, 3), activation='relu', padding="same",
                                        kernel_initializer="glorot_normal")(dlib_points_dist_input_layer)
        dlib_points_dist_layer = Conv2D(64, (1, 3), activation="relu", padding="same",
                                        kernel_initializer='glorot_normal')(dlib_points_dist_layer)
        # dlib_points_dist_layer = Conv2D(128,(1, 3),activation = "relu",padding="same",kernel_initializer='glorot_normal')(dlib_points_dist_layer)

        dlib_points_dist_layer = Flatten()(dlib_points_dist_layer)

        dlib_points_angle_input_layer = Input(shape=(1, 68, 1))
        dlib_points_angle_layer = Conv2D(32, (1, 3), activation='relu', padding="same",
                                         kernel_initializer="glorot_normal")(dlib_points_angle_input_layer)
        dlib_points_angle_layer = Conv2D(64, (1, 3), activation="relu", padding="same",
                                         kernel_initializer='glorot_normal')(dlib_points_angle_layer)
        # dlib_points_angle_layer = Conv2D(18,(1, 3),activation = "relu",padding="same",kernel_initializer='glorot_normal')(dlib_points_angle_layer)

        dlib_points_angle_layer = Flatten()(dlib_points_angle_layer)

        merged_layers = keras.layers.concatenate([dlib_points_layer, dlib_points_dist_layer, dlib_points_angle_layer])

        merged_layers = Dense(128, activation='relu')(merged_layers)
        # merged_layers = Dropout(0.2)(merged_layers)
        merged_layers = Dense(1024, activation='relu')(merged_layers)
        merged_layers = Dropout(0.2)(merged_layers)
        merged_layers = Dense(self.number_of_class, activation='softmax')(merged_layers)

        self.model = Model(
            inputs=[dlib_points_input_layer, dlib_points_dist_input_layer, dlib_points_angle_input_layer],
            outputs=merged_layers)
        self.built = True
        return self.model

    def train(self):
        """Traines the neuralnet model.      
        This method requires the following two directory to exist
        /PATH-TO-DATASET-DIR/train
        /PATH-TO-DATASET-DIR/test
        
        """
        assert self.built == True, "Model not built yet."

        self.model.compile(loss=keras.losses.categorical_crossentropy,
                           optimizer=keras.optimizers.Adam(LEARNING_RATE),
                           metrics=['accuracy'])
        # self.model.fit(x_train,y_train,epochs = EPOCHS, 
        #                 batch_size = BATCH_SIZE,validation_data=(x_test,y_test))
        self.preprocessor = self.preprocessor(DATA_SET_DIR)
        self.model.summary()
        self.model.fit_generator(self.preprocessor.flow(), steps_per_epoch=self.steps_per_epoch,
                                 epochs=self.epochs,
                                 validation_data=([self.preprocessor.test_dpoints, self.preprocessor.dpointsDists,
                                                   self.preprocessor.dpointsAngles],
                                                  self.preprocessor.test_image_emotions))
        score = self.model.evaluate(
            [self.preprocessor.test_dpoints, self.preprocessor.dpointsDists, self.preprocessor.dpointsAngles],
            self.preprocessor.test_image_emotions)
        self.save_model()
        self.logger.log_model(self.models_local_folder, score)

    def predict(self, face):
        """

        Args:
            face:

        Returns:

        """
        assert face.shape == IMG_SIZE, "Face image size should be " + str(IMG_SIZE)
        face = face.reshape(-1, 48, 48, 1)
        emotions = self.model.predict(face)[0]
        return emotions
