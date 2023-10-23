import copy
import torch
from torch import nn
import time
from torch.utils.data import DataLoader, Dataset
import gc

class DatasetSplit(Dataset):
    """An abstract Dataset class wrapped around Pytorch Dataset class.
    """

    def __init__(self, dataset, idxs):
        self.dataset = dataset
        self.idxs = [int(i) for i in idxs]

    def __len__(self):
        return len(self.idxs)

    def __getitem__(self, item):
        image, label = self.dataset[self.idxs[item]]
        return torch.tensor(image), torch.tensor(label)
def test_results(args, model, test_dataset):
    """ Returns the test accuracy and loss.
    """

    model.eval()
    loss, total, correct = 0.0, 0.0, 0.0

    device = 'cuda' if args.gpu else 'cpu'
    #criterion = nn.NLLLoss().to(device)
    criterion = nn.CrossEntropyLoss().to(device)
    testloader = DataLoader(test_dataset, batch_size=128,
                            shuffle=False)

    for batch_idx, (images, labels) in enumerate(testloader):
        gc.collect()
        torch.cuda.empty_cache()
        images, labels = images.to(device), labels.to(device)

        # Inference
        outputs = model(images)
        batch_loss = criterion(outputs, labels)
        loss += batch_loss.item()

        # Prediction
        _, pred_labels = torch.max(outputs, 1)
        pred_labels = pred_labels.view(-1)
        correct += torch.sum(torch.eq(pred_labels, labels)).item()
        total += len(labels)

    accuracy = correct/total
    return accuracy, loss

class ProxUpdate(object):
    def __init__(self, args, dataset, idxs, logger, local_epoch):
        self.args = args
        self.logger = logger
        self.local_ep = local_epoch
        self.trainloader, self.validloader, self.testloader = self.train_val_test(
            dataset, list(idxs))
        self.device = 'cuda' if args.gpu else 'cpu'
        # Default criterion set to NLL loss function
        if args.dataset == "cifar":
            self.criterion = nn.CrossEntropyLoss().to(self.device)
        else:
            self.criterion = nn.NLLLoss().to(self.device)

    def train_val_test(self, dataset, idxs):
        """
        Returns train, validation and test dataloaders for a given dataset
        and user indexes.
        """
        # split indexes for train, validation, and test (80, 10, 10)

        idxs_train = idxs[:int(0.8*len(idxs))]
        idxs_val = idxs[int(0.8*len(idxs)):int(0.9*len(idxs))]
        idxs_test = idxs[int(0.9*len(idxs)):]

        trainloader = DataLoader(DatasetSplit(dataset, idxs_train),
                                 batch_size=self.args.local_bs, shuffle=True)
        if len(idxs_val) < 10:
            validloader = DataLoader(DatasetSplit(dataset, idxs_val),
                                     batch_size=1, shuffle=False)
            testloader = DataLoader(DatasetSplit(dataset, idxs_test),
                                    batch_size=1, shuffle=False)
        else:
            validloader = DataLoader(DatasetSplit(dataset, idxs_val),
                                     batch_size=int(len(idxs_val)/10), shuffle=False)
            testloader = DataLoader(DatasetSplit(dataset, idxs_test),
                                    batch_size=int(len(idxs_test)/10), shuffle=False)

        return trainloader, validloader, testloader

    def update_weights(self, model, global_round):
        # Set mode to train model
        model.train()
        epoch_loss = []

        global_model = copy.deepcopy(model)
        start_time = time.time()

        decay = self.args.decay

        if decay != 0:
            learn_rate = self.args.lr * pow(decay, global_round)
        else:
            learn_rate = self.args.lr

        print(learn_rate)
        # Set optimizer for the local updates
        if self.args.optimizer == 'sgd':
            optimizer = torch.optim.SGD(model.parameters(), lr=(learn_rate),
                                        momentum=0.9, weight_decay=0.00001)
        elif self.args.optimizer == 'adam':
            optimizer = torch.optim.Adam(model.parameters(), lr=(learn_rate),
                                         weight_decay=1e-4)

        for iter in range(self.local_ep):
            batch_loss = []
            for batch_idx, (images, labels) in enumerate(self.trainloader):
                images, labels = images.to(self.device), labels.to(self.device)

                model.zero_grad()
                log_probs = model(images)

                proximal_term = 0.0
                # iterate through the current and global model parameters
                for w, w_t in zip(model.parameters(), global_model.parameters()):
                    # update the proximal term
                    # proximal_term += torch.sum(torch.abs((w-w_t)**2))
                    proximal_term += (w - w_t).norm(2)

                loss = self.criterion(log_probs, labels) + (self.args.mu / 2) * proximal_term

                loss.backward()
                optimizer.step()
                batch_loss.append(loss.item())

                if self.args.verbose and (batch_idx % 10 == 0):
                    print('| Global Round : {} | Local Epoch : {} | [{}/{} ({:.0f}%)]\tLoss: {:.6f}'.format(
                        global_round, iter, batch_idx * len(images),
                        len(self.trainloader.dataset),
                        100. * batch_idx / len(self.trainloader), loss.item()))
                self.logger.add_scalar('loss', loss.item())

            epoch_loss.append(sum(batch_loss)/len(batch_loss))
            gc.collect()
            torch.cuda.empty_cache()

        return model.state_dict(), sum(epoch_loss) / len(epoch_loss), time.time()- start_time

    def inference(self, model):
        """ Returns the inference accuracy and loss.
        """

        model.eval()
        loss, total, correct = 0.0, 0.0, 0.0

        for batch_idx, (images, labels) in enumerate(self.testloader):
            images, labels = images.to(self.device), labels.to(self.device)

            # Inference
            outputs = model(images)
            batch_loss = self.criterion(outputs, labels)
            loss += batch_loss.item()

            # Prediction
            _, pred_labels = torch.max(outputs, 1)
            pred_labels = pred_labels.view(-1)
            correct += torch.sum(torch.eq(pred_labels, labels)).item()
            total += len(labels)

        accuracy = correct/total
        return accuracy, loss