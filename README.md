## 目录结构
```angular2html
D:.
│  tree.txt
│  
│          
├─data
│  └─cifar
│      │  cifar-10-python.tar.gz
│      │  
│      └─cifar-10-batches-py
│              batches.meta
│              data_batch_1
│              data_batch_2
│              data_batch_3
│              data_batch_4
│              data_batch_5
│              readme.html
│              test_batch
│              
├─logs
│      events.out.tfevents.1697959675.Harrison
│      
├─save
│  │  fedPROX_cifar_resnet50_10_C[0.1]_iid[0]_E[10]_B[10]_LR[0.01]_mu[0.0]_%strag[0]_test_acc.png
│  │  fed_cifar_resnet50_10_C[0.1]_iid[0]_E[10]_B[10]_acc.png
│  │  fed_cifar_resnet50_10_C[0.1]_iid[0]_E[10]_B[10]_loss.png
│  │  
│  ├─csvResults
│  │      cifar_resnet50_10_C[0.1]_iid[0]_E[10]_B[10]_LR[0.01]_u[0.0]_%strag[0].csv
│  │      
│  └─objects
│          cifar_resnet50_10_C[0.1]_iid[0]_E[10]_B[10]_LR[0.01]_u[0.0]_%strag[0].pkl
│          
└─src
    │  args.py
    │  fedprox_main.py
    │  get_gpu_id.py
    │  models.py
    │  updates.py
    │  utils.py
```

## 文件内容解释

* `data`:**存储cifar数据**
* `logs`:**训练日志，使用`tensorboardX`前往`dashboard`可视化查看训练结果**
* `save`:**存储`accuracy`和`loss`以及测试的图像**
* `src`
  * `args.py`:参数配置
  * `fedprox_main.py`:运行`FedProx`算法进行迭代
  * `get_gpu_id.py`:获取`cpu id`
  * `models.py`:存储`resnet`相关模型
  * `updates.py`:定义了新的`FedProx`实例类和测试结果方法
  * `utils.py`:一些公用函数

## 示例运行命令 

更多参数设置可参考args.py
```angular2html
 python fedprox_main.py --dataset  cifar --gpu 0 --iid 0 --model resnet50 --pretrained yes
```

## TensorBoardX 打开命令
```angular2html
#进入logs文件夹下
tensorboard --dirlog=./
```


### 参考链接
https://github.com/weiaicunzai/pytorch-cifar100
https://github.com/ongzh/ScaffoldFL