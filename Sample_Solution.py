# -*- coding: utf-8 -*-
"""CS776_Assignment1.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1eqecsoDBAhF2NL58VXeDxT6EkNquaSSh

Training
"""

import torch
import torchvision
import torchvision.transforms as transforms
from torch.utils.data import DataLoader, random_split

# Define Transform (Normalization)
transform = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.5,), (0.5,))])

# Load Dataset
train_dataset = torchvision.datasets.FashionMNIST(root="./data", train=True, transform=transform, download=True)
test_dataset = torchvision.datasets.FashionMNIST(root="./data", train=False, transform=transform, download=True)

# Split Data
train_size = int(0.8 * len(train_dataset))
val_size = len(train_dataset) - train_size
train_data, val_data = random_split(train_dataset, [train_size, val_size])

# Data Loaders
batch_size = 64
train_loader = DataLoader(train_data, batch_size=batch_size, shuffle=True)
val_loader = DataLoader(val_data, batch_size=batch_size, shuffle=False)
test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

"""MLP"""

import torch.nn as nn
import torch.optim as optim

# Define MLP Model
class MLP(nn.Module):
    def __init__(self, input_size=784, hidden_sizes=[256, 128, 64], output_size=10):
        super(MLP, self).__init__()
        self.layers = nn.Sequential(
            nn.Linear(input_size, hidden_sizes[0]),
            nn.ReLU(),
            nn.Linear(hidden_sizes[0], hidden_sizes[1]),
            nn.ReLU(),
            nn.Linear(hidden_sizes[1], hidden_sizes[2]),
            nn.ReLU(),
            nn.Linear(hidden_sizes[2], output_size)
        )

    def forward(self, x):
        x = x.view(x.size(0), -1)  # Flattening
        return self.layers(x)

# Instantiate Model
mlp_model = MLP()
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(mlp_model.parameters(), lr=0.001)

# Training Loop
def train_model(model, train_loader, val_loader, criterion, optimizer, epochs=10):
    for epoch in range(epochs):
        model.train()
        for images, labels in train_loader:
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()  # Backpropagation
            optimizer.step()

        # Evaluate on validation data
        model.eval()
        val_loss = 0
        correct = 0
        total = 0
        with torch.no_grad():
            for images, labels in val_loader:
                outputs = model(images)
                val_loss += criterion(outputs, labels).item()
                _, predicted = torch.max(outputs, 1)
                correct += (predicted == labels).sum().item()
                total += labels.size(0)

        print(f"Epoch {epoch+1}, Loss: {loss.item()}, Validation Accuracy: {100 * correct / total:.2f}%")

train_model(mlp_model, train_loader, val_loader, criterion, optimizer)

"""CNN"""

import torch
import torch.nn as nn
import torch.optim as optim
import torchvision
import torchvision.transforms as transforms
from torch.utils.data import DataLoader

# ==============================
# 1️⃣ Dataset Preparation
# ==============================

# Define dataset transformation
transform = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.5,), (0.5,))])

# Load Fashion MNIST dataset
train_dataset = torchvision.datasets.FashionMNIST(root="./data", train=True, transform=transform, download=True)
test_dataset = torchvision.datasets.FashionMNIST(root="./data", train=False, transform=transform, download=True)

# Split dataset into training and validation sets
train_size = int(0.8 * len(train_dataset))
val_size = len(train_dataset) - train_size
train_data, val_data = torch.utils.data.random_split(train_dataset, [train_size, val_size])

# Create data loaders
batch_size = 64
train_loader = DataLoader(train_data, batch_size=batch_size, shuffle=True)
val_loader = DataLoader(val_data, batch_size=batch_size, shuffle=False)
test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

# ==============================
# 2️⃣ Define CNN Model
# ==============================

class CNN(nn.Module):
    def __init__(self, num_classes=10, pooling_type="max"):
        super(CNN, self).__init__()

        # Define convolutional layers
        self.conv1 = nn.Conv2d(1, 32, kernel_size=3, stride=1, padding=1)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1)
        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, stride=1, padding=1)
        self.conv4 = nn.Conv2d(128, 256, kernel_size=3, stride=1, padding=1)
        self.conv5 = nn.Conv2d(256, 512, kernel_size=3, stride=1, padding=1)

        self.relu = nn.ReLU()

        # Choose pooling method
        if pooling_type == "max":
            self.pool = nn.MaxPool2d(kernel_size=2, stride=2)
        elif pooling_type == "average":
            self.pool = nn.AvgPool2d(kernel_size=2, stride=2)
        elif pooling_type == "global":
            self.pool = nn.AdaptiveAvgPool2d((1, 1))

        # Automatically compute flattened size
        self.flattened_size = self._compute_flattened_size()

        # Fully connected layer
        self.fc = nn.Linear(self.flattened_size, num_classes)

    def _compute_flattened_size(self):
        """Pass a dummy input to compute the flattened feature size for the fully connected layer"""
        with torch.no_grad():
            dummy_input = torch.zeros(1, 1, 28, 28)  # One image of size 28x28
            output = self.forward_features(dummy_input)
        return output.view(-1).shape[0]

    def forward_features(self, x):
        """Extract features before passing to the fully connected layer"""
        x = self.relu(self.conv1(x))
        x = self.pool(x)
        x = self.relu(self.conv2(x))
        x = self.pool(x)
        x = self.relu(self.conv3(x))
        x = self.relu(self.conv4(x))
        x = self.relu(self.conv5(x))

        print(f"Feature map shape before flattening: {x.shape}")  # Debugging output
        x = torch.flatten(x, 1)
        print(f"Feature map shape after flattening: {x.shape}")  # Debugging output
        return x

    def forward(self, x):
        x = self.forward_features(x)
        x = self.fc(x)
        return x

# ==============================
# 3️⃣ Weight Initialization
# ==============================

def initialize_weights(model, init_type="xavier"):
    """Initialize weights using different strategies"""
    for layer in model.modules():
        if isinstance(layer, nn.Conv2d):
            if init_type == "xavier":
                nn.init.xavier_uniform_(layer.weight)
            elif init_type == "he":
                nn.init.kaiming_uniform_(layer.weight, nonlinearity='relu')
            elif init_type == "random":
                nn.init.normal_(layer.weight, mean=0, std=0.1)

# ==============================
# 4️⃣ Training Function
# ==============================

def train_model(model, train_loader, val_loader, criterion, optimizer, epochs=10):
    """Train and validate the CNN model"""
    model.train()

    for epoch in range(epochs):
        total_loss = 0
        correct, total = 0, 0

        print(f"Epoch {epoch+1} started...")  # Debugging statement

        for batch_idx, (images, labels) in enumerate(train_loader):
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            _, predicted = torch.max(outputs, 1)
            correct += (predicted == labels).sum().item()
            total += labels.size(0)

            if batch_idx % 10 == 0:  # Print every 10 batches
                print(f"Batch {batch_idx}: Loss={loss.item()}")

        # Validation Step
        model.eval()
        val_correct, val_total = 0, 0
        with torch.no_grad():
            for images, labels in val_loader:
                outputs = model(images)
                _, predicted = torch.max(outputs, 1)
                val_correct += (predicted == labels).sum().item()
                val_total += labels.size(0)

        val_accuracy = 100 * val_correct / val_total
        print(f"Epoch {epoch+1}, Loss: {total_loss:.4f}, Validation Accuracy: {val_accuracy:.2f}%\n")

# ==============================
# 5️⃣ Running the Model
# ==============================

# Device Configuration
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

# Instantiate Model
cnn_model = CNN(pooling_type="max").to(device)

# Initialize Weights
initialize_weights(cnn_model, init_type="he")

# Define Loss Function and Optimizer
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(cnn_model.parameters(), lr=0.001)

# Train the Model
train_model(cnn_model, train_loader, val_loader, criterion, optimizer, epochs=10)

"""Different Initializations of weights"""

def initialize_weights(model, init_type="xavier"):
    for layer in model.modules():
        if isinstance(layer, nn.Conv2d):
            if init_type == "xavier":
                nn.init.xavier_uniform_(layer.weight)
            elif init_type == "he":
                nn.init.kaiming_uniform_(layer.weight, nonlinearity='relu')
            elif init_type == "random":
                nn.init.normal_(layer.weight, mean=0, std=0.1)

# Example Usage
cnn_model = CNN()
initialize_weights(cnn_model, init_type="he")  # Using He Initialization