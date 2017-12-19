from config import SESSION,IMG_SIZE
from train_config import INPUT_SHAPE
from nets.base import NeuralNet
from test_config import TEST_TYPE, TEST_IMAGE
import cv2
import dlib
from util import SevenEmotionsClassifier
from preprocess.base import Preprocessor
from postprocess.base import PostProcessor
from preprocess.multinput import MultiInputPreprocessor
from nets.multinput import MultiInputNeuralNet
from nets.rnn import LSTMNet
from train_config import NETWORK_TYPE,AUGMENTATION
from preprocess.sequencial import SequencialPreprocessor
from process.sequencial import EmopySequencialProcess
from nets.vggface import VGGFaceEmopyNet
import numpy as np
def run():
    if SESSION == 'train':
        run_train()
    elif SESSION == 'test':
        run_test()
def run_train():
    # input_shape = (IMG_SIZE[0],IMG_SIZE[1],1)
    input_shape = INPUT_SHAPE
    classifier = SevenEmotionsClassifier()
    if(NETWORK_TYPE == "mi"):
        preprocessor = MultiInputPreprocessor(classifier,input_shape = input_shape,augmentation = AUGMENTATION)
        neuralNet = MultiInputNeuralNet(input_shape,preprocessor=preprocessor,train=True)
    elif NETWORK_TYPE == "si":
        preprocessor = Preprocessor(classifier,input_shape = input_shape,augmentation = AUGMENTATION)
        neuralNet = NeuralNet(input_shape,preprocessor=preprocessor,train=True)
    elif NETWORK_TYPE =="rnn":
        preprocessor = SequencialPreprocessor(classifier,input_shape = input_shape,augmentation = AUGMENTATION)("dataset/ck-split")
        neuralNet = LSTMNet(input_shape,preprocessor=preprocessor,train=True)
    elif NETWORK_TYPE == "vgg":
        preprocessor = Preprocessor(classifier,input_shape = input_shape,augmentation = AUGMENTATION)
        neuralNet = VGGFaceEmopyNet(input_shape,preprocessor=preprocessor,train=True)
        
    
    else:
        process = EmopySequencialProcess(input_shape,6)
        process.process_video("/home/mtk/iCog/projects/emopy/test-videos/75Emotions.mp4")

    neuralNet.train()   


def run_test():
    input_shape = (IMG_SIZE[0],IMG_SIZE[1],1)   
    classifier = SevenEmotionsClassifier()
    preprocessor = Preprocessor(classifier,input_shape = input_shape)
    postProcessor = PostProcessor(classifier)
    neuralNet = NeuralNet(input_shape,preprocessor = preprocessor,train = False)
    face_detector = dlib.get_frontal_face_detector()

    if TEST_TYPE=="image":
        img = cv2.imread(TEST_IMAGE)
        faces,rectangles = preprocessor.get_faces(img,face_detector)
        predictions = []
        for i in range(len(faces)):
            face = preprocessor.sanitize(faces[i])
            predictions.append(neuralNet.predict(face))

        postProcessor = postProcessor(img,rectangles,predictions)
        cv2.imshow("Image",img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    
    elif TEST_TYPE =="video":
        pass
    elif TEST_TYPE == "webcam":
        cap =  cv2.VideoCapture(-1)
        while cap.isOpened():
            ret, frame = cap.read()
            faces,rectangles = preprocessor.get_faces(frame,face_detector)
            if len(faces)>0:
                emotions = []
                for i in range(len(faces)):
                    face_i = faces[i]
                    resized = cv2.resize(face_i,(INPUT_SHAPE[0],INPUT_SHAPE[1]))
                    # resized = preprocessor.sanitize(resized)
                    print resized.shape
                    resized = resized.astype(np.float32)/255
                    predictions = neuralNet.predict(resized)
                    print predictions
                    emotion = postProcessor.arg_max(predictions)
                    emotions.append(preprocessor.classifier.get_string(emotion))
                postProcessor.overlay(frame,rectangles,emotions)
            cv2.imshow("Image",frame)
            if (cv2.waitKey(10) & 0xFF == ord('q')):
                break
            


    