import gym
import random
import torch
import torch.nn as nn
import numpy as np

from tqdm import tqdm



def strategy_raw(status):
    action=random.choice((0,1))
    return action
class critic(nn.Module):
    
    def __init__(self):
        super().__init__()
        self.fc1= nn.Linear(4, 36)
        # self.fc2= nn.Linear(36, 36)
        self.fc3= nn.Linear(36, 2)
    def forward(self,x):
        out=self.fc1(x)
      
        out=torch.tanh(self.fc3(out))
      
        return out

class actor(nn.Module):
    
    def __init__(self):
        super().__init__()
        self.fc1= nn.Linear(4, 36)
        # self.fc2= nn.Linear(36, 36)
        self.fc3= nn.Linear(36, 2)
    def forward(self,x):
        out=torch.relu(self.fc1(x))
        # out=self.fc2(out)
        out=self.fc3(out)
        
        
        out=torch.nn.Softmax(dim=0)(out)
        return out
   

def accumulate(s,reward):
    result=0
    for i in range(0,len(reward)-s):

        result+=reward[i]*pow(0.9,i)
    return result

def gen_reward(reward):  
     n_reward=[]
     for i in range(len(reward)):
         n_reward.append(accumulate(i,reward))
     return n_reward


device=torch.device('cuda:0')
     
model=actor().to(device)    
cmodel=critic().to(device)

env = gym.make('CartPole-v0')
env._max_episode_steps = 500
status = env.reset()

count=0

action_set=[]
reward_set=[]
status_set=[]
discount=0.9

print('collecting data')
for i in tqdm(range(100)):
    status = env.reset()  
    raw_reward_set=[]
    done=False
    while not done:
        status_set.append(status)
    
    
    
        count+=1
        # env.render()
        action=strategy_raw(status)
    
        action_set.append(action)
        status,reward,done,_=env.step(action)
    
    # if done:
    #     reward=0
    
        raw_reward_set.append(reward)
    
    # print(model(torch.tensor(status).to(torch.float32)))
    raw_reward_set=gen_reward(raw_reward_set)
    reward_set.extend(raw_reward_set)

actions=torch.tensor(action_set).to(torch.float32).to(device)

rewards=np.array(reward_set)
# rewards=rewards-sum(rewards)/len(rewards)

reward_mean = np.mean(rewards)
reward_std = np.std(rewards)
rewards= (rewards - reward_mean) / reward_std



rewards=torch.tensor(rewards).to(torch.float32).to(device)

statuses=torch.tensor(status_set)

optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

coptimizer = torch.optim.Adam(cmodel.parameters(), lr=0.001)



def test_count():
  model.eval()


  status = env.reset()  
    
  done=False
  count=0
  while not done:
        count+=1
        #env.render()
        
        x=torch.tensor(status).to(torch.float32).to(device)
        y=model(x)
        m=torch.distributions.Categorical(y)
        
        
        action=int(m.sample().item())

        #print(action)
        # action=strategy_raw(status)
    
        status,reward,done,_=env.step(action)
        
  print('count',count)
class loss_set:
    def __init__(self):
        self.sum=0
        self.n=0
    def add(self,num):
        self.sum+=num
        self.n+=1
    def show(self):
        out=self.sum/self.n
        self.sum=0
        self.n=0
        return out
    
mloss=loss_set()

criterion= torch.nn.MSELoss()


num_epochs=200000

for epoch in range(num_epochs):
  test_count()
  model.train()
  for i in range(len(actions)-1):
    
    
    
    
    prob=model(statuses[i].to(torch.float32).to(device))
    
    m=torch.distributions.Categorical(prob)
   
    pred_q=cmodel(statuses[i].to(torch.float32).to(device))[int(actions[i].item())]
    
    
    next_q=cmodel(statuses[i+1].to(torch.float32).to(device))[int(actions[i+1].item())]
    target_q=1+discount*next_q
    
    
    
    #loss=-m.log_prob(actions[i])*rewards[i]
    if i%10==0:
        optimizer.zero_grad()
        loss=-torch.pow(np.e,m.log_prob(actions[i]))*rewards[i]/0.5
        loss.backward(retain_graph=True)
        optimizer.step()
        
    coptimizer.zero_grad()    
    closs=criterion(pred_q,target_q)
    
    closs.backward()
    
    
    
    
    
    coptimizer.step()
    
    mloss.add(loss.item())
    if (i+1) % 200 == 0:
            print ('Epoch [{}/{}], Step [{}/{}], Loss: {:.4f}' 
                    .format(epoch+1, num_epochs, i+1, len(actions), mloss.show()))
# rewards=torch.tensor(rewards)








# torch.save(model.state_dict(), 'pole_raw.pth')  
