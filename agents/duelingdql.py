import os

import tensorflow as tf
import tensorflow.keras as kr

import random
import numpy as np
from util import *

from gameEngine import AGENT_INPUT_SIZE

SAVE_PATH = "dueling-deep-q-learner-save.h5"

# Tillåts att gå 10% över denna
SOFT_REPLAY_LIMIT = 50000

TRAIN_RATE = 500
BATCH_SIZE = 10240

ACTIONS = [Actions.LEFT, Actions.RIGHT, Actions.JUMP, Actions.NONE]


def elu(x, alpha):
    return np.where(x > 0, x, alpha * (np.exp(x) - 1))


class DuelingModel(kr.models.Model):
    def __init__(self):
        super(DuelingModel, self).__init__()

        # Common layers
        self.clayer1 = kr.layers.Dense(4,
                                       bias_initializer=None,
                                       activation=kr.activations.elu)
        # Advantage specific
        self.alayer = kr.layers.Dense(len(ACTIONS),
                                      bias_initializer=None,
                                      activation=kr.activations.linear)

        # Value specific
        self.vlayer = kr.layers.Dense(1,
                                      bias_initializer=None,
                                      activation=kr.activations.linear)

    def call(self, x):
        x = self.clayer1(x)

        a = self.alayer(x)
        v = self.vlayer(x)[0]

        return (a, v)

    def call_fast(self, x):
        # Om vi bara kör på ett spel, så tar det mer tid att använda tensorflow
        # C.a. 2x snabbare än self.call

        # Anta alpha == 1 för elu, verkar stämma
        l1k, l1b = self.clayer1.kernel.numpy(), self.clayer1.bias.numpy()
        x = elu(l1b + np.dot(x, l1k), 1)

        al1k, al1b = self.alayer.kernel.numpy(), self.alayer.bias.numpy()
        a = al1b + np.dot(x, al1k)

        vl1k, vl1b = self.vlayer.kernel.numpy(), self.vlayer.bias.numpy()
        v = vl1b + np.dot(x, vl1k)

        return (a, v)

    def get_q(self, x):
        adv, val = self.call(x)
        val_tiled = tf.tile(tf.reshape(val, (-1, 1)), [1, len(ACTIONS)])
        mean = tf.math.reduce_mean(adv, axis=1)
        mean_tiled = tf.tile(tf.reshape(mean, (-1, 1)), [1, len(ACTIONS)])

        return val_tiled + adv - mean_tiled


class DuelingDQL:
    def __init__(self,
                 random_action_method,
                 future_discount=0.75,
                 learning_rate=0.001,
                 saveAndLoad=True):
        learning_rate = learning_rate * (1 - future_discount) / (1 - 0.8)

        self.model = DuelingModel()
        self.model.build((None, AGENT_INPUT_SIZE))

        self.saveAndLoad = saveAndLoad

        if os.path.isfile(SAVE_PATH) and saveAndLoad:
            #print("Loading")
            self.model.load_weights(SAVE_PATH)
        else:
            pass#print("Creating new model")

        # Står om detta i Atari-pappret
        # Basically en pool av alla saker som har hänt i alla spel
        # Varje gång träning händer så dras en slumpmässig batch härifrån
        # Består av: (agent_input, action, agent_input_after, reward)
        self.experience_replay = [
            np.zeros(shape=(SOFT_REPLAY_LIMIT, AGENT_INPUT_SIZE)),  # Input
            np.zeros(shape=(SOFT_REPLAY_LIMIT)),  # Action
            np.zeros(shape=(SOFT_REPLAY_LIMIT, AGENT_INPUT_SIZE)),  # Input after
            np.zeros(shape=(SOFT_REPLAY_LIMIT)),  # Reward
        ]
        self.experience_replay_index = 0

        self.highest_er = 0

        self.random_action_method = random_action_method

        self.learning_rate = learning_rate
        self.future_discount = future_discount

        self.loss_measure = tf.losses.MeanSquaredError()
        self.opt = tf.optimizers.Adam(lr=self.learning_rate)

        self.n_since_last_train = 0

        self.latestLoss = tf.add(0, 0)

    def getAction(self, agentInput):
        rand_action = self.random_action_method.get_random_action()
        if rand_action is not None:
            return rand_action
        else:
            adv, val = self.model.call_fast(agentInput)
            return ACTIONS[np.argmax(adv)]

    def update(self, oldAgentInput, action, newAgentInput, reward):
        # Lägg till i experience_replay
        self.experience_replay[0][self.experience_replay_index] = oldAgentInput
        self.experience_replay[1][self.experience_replay_index] = ACTIONS.index(action)
        self.experience_replay[2][self.experience_replay_index] = newAgentInput
        self.experience_replay[3][self.experience_replay_index] = reward
        self.experience_replay_index = (self.experience_replay_index + 1) % SOFT_REPLAY_LIMIT

        self.highest_er = max(self.highest_er, self.experience_replay_index)

        self.n_since_last_train += 1

        if self.n_since_last_train > TRAIN_RATE:
            #print("Training")
            loss = self.train_on_random_minibatch()
            #print("Loss =", loss)
            if self.saveAndLoad:
                self.model.save_weights(SAVE_PATH)

            self.n_since_last_train = 0

    def train_on_random_minibatch(self):
        idxs = np.random.randint(self.highest_er, size=(BATCH_SIZE, ))

        loss = self.train_on_batch(
            self.experience_replay[0][idxs],
            self.experience_replay[1][idxs],
            self.experience_replay[2][idxs],
            self.experience_replay[3][idxs],
        )
        return loss.numpy()

    def train_on_batch(self, agent_input_before, action, agent_input_after,
                       reward):
        q_after = self.model.get_q(agent_input_after)
        wanted_q = reward + self.future_discount * tf.reduce_max(q_after, axis=1)
        #wanted_q = reward

        tvars = self.model.trainable_variables

        with tf.GradientTape() as tape:
            pred_q_for_all_actions = self.model.get_q(agent_input_before)

            # Indexera med rätt actions
            action_ind = tf.transpose(
                [tf.range(agent_input_before.shape[0]), action])
            pred_q_for_action = tf.gather_nd(pred_q_for_all_actions,
                                             action_ind)

            loss = self.loss_measure(wanted_q, pred_q_for_action)

            gradients = tape.gradient(loss, tvars)
        self.opt.apply_gradients(zip(gradients, tvars))

        self.latestLoss = loss
        return loss
