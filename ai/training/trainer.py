import torch
import torch.nn as nn
from tqdm import tqdm


class Trainer:

    def __init__(
        self,
        model,
        train_loader,
        valid_loader,
        criterion,
        optimizer,
        device,
    ):

        self.model = model.to(device)

        self.train_loader = train_loader

        self.valid_loader = valid_loader

        self.criterion = criterion

        self.optimizer = optimizer

        self.device = device

    def train_one_epoch(self):

        self.model.train()

        running_loss = 0

        correct = 0

        total = 0

        for images, labels in tqdm(self.train_loader):

            images = images.to(self.device)

            labels = labels.to(self.device)

            self.optimizer.zero_grad()

            outputs = self.model(images)

            loss = self.criterion(outputs, labels)

            loss.backward()

            self.optimizer.step()

            running_loss += loss.item()

            _, predicted = outputs.max(1)

            total += labels.size(0)

            correct += predicted.eq(labels).sum().item()

        accuracy = 100 * correct / total

        loss = running_loss / len(self.train_loader)

        return loss, accuracy

    @torch.no_grad()
    def validate(self):

        self.model.eval()

        running_loss = 0

        correct = 0

        total = 0

        for images, labels in tqdm(self.valid_loader):

            images = images.to(self.device)

            labels = labels.to(self.device)

            outputs = self.model(images)

            loss = self.criterion(outputs, labels)

            running_loss += loss.item()

            _, predicted = outputs.max(1)

            total += labels.size(0)

            correct += predicted.eq(labels).sum().item()

        accuracy = 100 * correct / total

        loss = running_loss / len(self.valid_loader)

        return loss, accuracy