from model import *
from torch.utils.data import DataLoader, TensorDataset
import time

import torch.optim as optim



def train(X_train, y_train):
    X_train = torch.tensor(X_train)
    y_train = torch.tensor(y_train)

    train_dataset = TensorDataset(X_train, y_train)
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=False)


    model = LSTM(input_size, hidden_size, num_layers, output_size).to(device)

    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)


    loss_values = [] # loss 값을 저장할 리스트
    
    print("train...")
    for epoch in range(num_epochs):
        start_time = time.time()  # 시작 시간 저장
        running_loss = 0.0
        for i, (inputs, labels) in enumerate(train_loader):
            inputs = inputs.float().to(device)
            labels = labels.float().to(device)

            outputs = model(inputs)
            optimizer.zero_grad()

            loss = criterion(outputs, labels)

            loss.backward()
            optimizer.step()

            running_loss += loss.item()
        
        
        epoch_loss = running_loss / len(train_loader)
        loss_values.append(epoch_loss) # epoch_loss 값 리스트에 추가
        end_time = time.time()  # 종료 시간 저장
        epoch_time = end_time - start_time  # 한 에폭에 걸린 시간
        
        print('Epoch [{}/{}], Loss: {:.4f}, Time: {:.2f}s'.format(epoch+1, num_epochs, epoch_loss, epoch_time))

    print("Finished!")
    
