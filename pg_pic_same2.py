import gym
import random
import torch
import torch.nn as nn
import numpy as np

from tqdm import tqdm




import torchvision.transforms as T


from PIL import Image


device=torch.device('cuda:0')

resize = T.Compose([T.ToPILImage(),
                    T.Resize(40, interpolation=Image.CUBIC),
                    T.ToTensor()])


# torch.manual_seed(1423)
def get_cart_location(screen_width):
    world_width = env.x_threshold * 2
    scale = screen_width / world_width
    return int(env.state[0] * scale + screen_width / 2.0)  # MIDDLE OF CART

def get_screen():
    # Returned screen requested by gym is 400x600x3, but is sometimes larger
    # such as 800x1200x3. Transpose it into torch order (CHW).
    screen = env.render(mode='rgb_array').transpose((2, 0, 1))
    #print(env)
    # Cart is in the lower half, so strip off the top and bottom of the screen
    _, screen_height, screen_width = screen.shape
    screen = screen[:, int(screen_height*0.4):int(screen_height * 0.8)]
    view_width = int(screen_width * 0.6)
    cart_location = get_cart_location(screen_width)
    if cart_location < view_width // 2:
        slice_range = slice(view_width)
    elif cart_location > (screen_width - view_width // 2):
        slice_range = slice(-view_width, None)
    else:
        slice_range = slice(cart_location - view_width // 2,
                            cart_location + view_width // 2)
    # Strip off the edges, so that we have a square image centered on a cart
    screen = screen[:, :, slice_range]
    # Convert to float, rescale, convert to torch tensor
    # (this doesn't require a copy)
    screen = np.ascontiguousarray(screen, dtype=np.float32) / 255
    screen = torch.from_numpy(screen)
    # Resize, and add a batch dimension (BCHW)
    return resize(screen).unsqueeze(0)








def strategy_raw(status):
    model.eval()
    y=model(status.to(device))
        
    a=torch.distributions.Categorical(y)
        
    action=int(a.sample().item())
    return action
    
   


class NN(nn.Module):  
    def __init__(self):
        super().__init__()
        self.shape=1
        self.c1=nn.Conv2d(12,16,5,2,1)
        self.n1=nn.BatchNorm2d(16)
        
        self.c2=nn.Conv2d(16,32,3,2,1)
        self.n2=nn.BatchNorm2d(32)
        
        self.c3=nn.Conv2d(32,32,3,3,1)
        self.n3=nn.BatchNorm2d(32)
        
        self.c4=nn.Conv2d(32,32,3,3,1)
        self.n4=nn.BatchNorm2d(32)
        
        
        
        self.fc1= nn.Linear(192, 64)
        self.fc3= nn.Linear(64, 2)
    def forward(self,x):
        
        
        out=self.c1(x)
        out=self.n1(out)
        out=nn.functional.relu(out)
        
        out=self.c2(out)
        out=self.n2(out)
        out=nn.functional.relu(out)
        
        out=self.c3(out)
        out=self.n3(out)
        out=nn.functional.relu(out)
        
        out=self.c4(out)
        out=self.n4(out)
        out=nn.functional.relu(out)
        
        
        out=out.view(out.size()[0],-1)
    
        
        out=self.fc1(out)
     
        out=torch.relu(out)
        out=self.fc3(out)
        out=nn.Softmax(dim=1)(out)
      
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


     
model=NN().to(device)  
        

env = gym.make('CartPole-v0')
env._max_episode_steps = 500
status = env.reset()

count=0

action_set=[]
reward_set=[]
status_set=[]
discount=0.9

print('collecting data')


def stack_work(series):
    s=[]
    for j in range(len(series)):
        
       if j>4:
           s.append(torch.cat((series[j].squeeze(),series[j-1].squeeze(),series[j-2].squeeze(),series[j-3].squeeze())).unsqueeze(0))
 
           
       else:
           s.append(torch.cat((series[j].squeeze(),series[j].squeeze(),series[j].squeeze(),series[j].squeeze())).unsqueeze(0))
    return s
        
  
    
    



def collect_data(times):
  count=0
  for i in range(times):
    status = env.reset()  
    raw_reward_set=[]
    done=False
    while not done:
        status_set.append(get_screen())
        count+=1
        if count<4:
            action=strategy_raw(torch.cat((get_screen().squeeze(),get_screen().squeeze(),get_screen().squeeze(),get_screen().squeeze())).unsqueeze(0))
        else:
            action=strategy_raw(torch.cat((status_set[-1].squeeze(),status_set[-2].squeeze(),status_set[-3].squeeze(),status_set[-4].squeeze())).unsqueeze(0))
        action_set.append(action)
        status,reward,done,_=env.step(action)
    
    # if done:
    #     reward=0
    
        raw_reward_set.append(reward)
    
    # print(model(torch.tensor(status).to(torch.float32)))
    raw_reward_set=gen_reward(raw_reward_set)
    reward_set.extend(raw_reward_set)

  actions=torch.tensor(action_set).to(torch.float32)

  rewards=np.array(reward_set)
# rewards=rewards-sum(rewards)/len(rewards)

  reward_mean = np.mean(rewards)
  reward_std = np.std(rewards)
  rewards= (rewards - reward_mean) / reward_std



  rewards=torch.tensor(rewards).to(torch.float32)
  print(count/times)
  return status_set,actions,rewards

# statuses=torch.tensor(status_set)
optimizer = torch.optim.Adam(model.parameters(), lr=0.01)


from torch.utils.data import Dataset, DataLoader


class my_dataset(Dataset):

    def __init__(self,status_set,actions,rewards):
       self.status = status_set
       self.actions= actions
       self.rewards= rewards
    def __len__(self):
       return len(self.status)

    def __getitem__(self, idx):
       
    
     
        
        
        return self.status[idx].squeeze(),self.actions[idx],self.rewards[idx]



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


for centry in tqdm(range(100)):
  num_epochs=1
  status_set,actions,rewards=collect_data(128)
  
  status_sets=stack_work(status_set)
  
  mydata=my_dataset(status_sets,actions,rewards)

  dataloader = DataLoader(mydata, batch_size=128, shuffle=True, num_workers=4)



  for epoch in range(num_epochs):
    # test_count()
    model.train()
    for status,action,reward in dataloader:
        optimizer.zero_grad()
    
    
        prob=model(status.to(torch.float32).to(device))
    
        m=torch.distributions.Categorical(prob)
   
   
        # loss=-torch.pow(np.e,m.log_prob(action.to(device)))*reward.to(device)/0.5
        loss=-m.log_prob(action.to(device))*reward.to(device)
        loss=loss.sum()
    # loss=m.log_prob(actions[i])*rewards[i]
    
    
        loss.backward()
        optimizer.step()

# torch.save(model.state_dict(), '1.pt')
