Problem:
Generate a CNN model in PyTorch for image classification (28x28 grayscale images, 10 classes).

Reference Solution:
```python
import torch
import torch.nn as nn


class SimpleCNN(nn.Module):
    def __init__(self, num_classes=10):
        super().__init__()

        # Convolution layers learn the image features
        self.features = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),                      # 28x28 -> 14x14
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),                      # 14x14 -> 7x7
        )

        # Fully connected layers make the final decision
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(64 * 7 * 7, 128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, num_classes),
        )

    def forward(self, x):
        x = self.features(x)
        return self.classifier(x)


model = SimpleCNN()
fake_images = torch.randn(4, 1, 28, 28)
print(model(fake_images).shape)    # torch.Size([4, 10])
```

Train it with nn.CrossEntropyLoss() and torch.optim.Adam(model.parameters(), lr=0.001).
