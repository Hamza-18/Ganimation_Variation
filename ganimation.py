import itertools
import torch
from base_model import BaseModel
import model_utils


class GANimationModel(BaseModel):
    """docstring for GANimationModel"""
    def __init__(self):
        super(GANimationModel, self).__init__()
        self.name = "GANimation"

    def initialize(self, opt):
        super(GANimationModel, self).initialize(opt)

        self.net_gen = model_utils.define_splitG(self.opt.img_nc, self.opt.aus_nc, self.opt.ngf, use_dropout=self.opt.use_dropout, 
                    norm=self.opt.norm, init_type=self.opt.init_type, init_gain=self.opt.init_gain, gpu_ids=self.gpu_ids)
        self.models_name.append('gen')
        self.net_gen_pose = model_utils.define_splitG(self.opt.img_nc, self.opt.pose_nc, self.opt.ngf, use_dropout=self.opt.use_dropout, 
                    norm=self.opt.norm, init_type=self.opt.init_type, init_gain=self.opt.init_gain, gpu_ids=self.gpu_ids)
        self.models_name.append('gen_pose')
        
        if self.is_train:
            self.net_dis = model_utils.define_splitD(self.opt.img_nc, self.opt.aus_nc, self.opt.final_size, self.opt.ndf, 
                    norm=self.opt.norm, init_type=self.opt.init_type, init_gain=self.opt.init_gain, gpu_ids=self.gpu_ids)
            self.models_name.append('dis')
            self.net_dis_pose = model_utils.define_splitD(self.opt.img_nc, self.opt.pose_nc, self.opt.final_size, self.opt.ndf, 
                    norm=self.opt.norm, init_type=self.opt.init_type, init_gain=self.opt.init_gain, gpu_ids=self.gpu_ids)
            self.models_name.append('dis_pose')

        if self.opt.load_epoch > 0:
            self.load_ckpt(self.opt.load_epoch)

    def setup(self):
        super(GANimationModel, self).setup()
        if self.is_train:
            # setup optimizer
            self.optim_gen = torch.optim.Adam(itertools.chain(self.net_gen.parameters(), self.net_gen_pose.parameters()),
                            lr=self.opt.lr, betas=(self.opt.beta1, 0.999))
            self.optims.append(self.optim_gen)
            
            self.optim_dis = torch.optim.Adam(itertools.chain(self.net_dis.parameters(), self.net_dis_pose.parameters()), 
                            lr=self.opt.lr, betas=(self.opt.beta1, 0.999))
            
            self.optims.append(self.optim_dis)

            # setup schedulers
            self.schedulers = [model_utils.get_scheduler(optim, self.opt) for optim in self.optims]

    def feed_batch(self, batch):
        self.src_img = batch['src_img'].to(self.device)
        self.tar_aus = batch['tar_aus'].type(torch.FloatTensor).to(self.device)
        self.tar_pose = batch['tar_pose'].type(torch.FloatTensor).to(self.device)
        if self.is_train:
            self.src_aus = batch['src_aus'].type(torch.FloatTensor).to(self.device)
            self.src_pose = batch['src_pose'].type(torch.FloatTensor).to(self.device)
            self.tar_img = batch['tar_img'].to(self.device)

    def forward(self):
        # generate fake image
        self.color_mask ,self.aus_mask, self.embed = self.net_gen(self.src_img, self.tar_aus)
        self.fake_img = self.aus_mask * self.src_img + (1 - self.aus_mask) * self.color_mask # formula given in research paper

        # reconstruct real image
        if self.is_train:
            self.rec_color_mask, self.rec_aus_mask, self.rec_embed = self.net_gen(self.fake_img, self.src_aus)
            self.rec_real_img = self.rec_aus_mask * self.fake_img + (1 - self.rec_aus_mask) * self.rec_color_mask

     #------------------------------------    
    # new method for the generator
    #------------------------------------
    
    # feed forward the fake image to change the pose
    def forward_pose(self):
        self.color_mask_pose, self.aus_mask_pose, self.embed_pose = self.net_gen_pose(self.fake_img, self.tar_pose)
        self.fake_img_pose = self.aus_mask_pose * self.fake_img + (1 - self.aus_mask_pose) * self.color_mask_pose

        # identity loss
        if self.is_train:
            self.rec_color_mask_pose, self.rec_aus_mask_pose, self.rec_embed_pose = self.net_gen_pose(self.fake_img_pose, self.src_pose)
            self.rec_real_img_pose = self.rec_aus_mask_pose * self.fake_img_pose + (1 - self.rec_aus_mask_pose) * self.rec_color_mask_pose

     #------------------------------------    
    # new method for the discriminator
    #------------------------------------

    def backward_dis_pose(self):
        # real image
        pred_real_pose, self.pred_real_aus_pose = self.net_dis_pose(self.src_img)
        self.loss_dis_real_pose = self.criterionGAN(pred_real_pose, True)
        self.loss_dis_real_aus_pose = self.criterionMSE(self.pred_real_aus_pose, self.src_pose)

        # fake image, detach to stop backward to generator
        pred_fake_pose, _ = self.net_dis_pose(self.fake_img_pose.detach()) 
        self.loss_dis_fake_pose = self.criterionGAN(pred_fake_pose, False)

        # combine dis loss
        self.loss_dis_pose =   self.opt.lambda_dis * (self.loss_dis_fake_pose + self.loss_dis_real_pose) \
                        + self.opt.lambda_aus * self.loss_dis_real_aus_pose
        if self.opt.gan_type == 'wgan-gp':
            self.loss_dis_gp_pose = self.gradient_penalty(self.src_img, self.fake_img_pose)
            self.loss_dis_pose = self.loss_dis_pose + self.opt.lambda_wgan_gp * self.loss_dis_gp_pose
        
        # backward discriminator loss
        self.loss_dis_pose.backward(retain_graph=True)

    def backward_dis(self):
        # real image
        pred_real, self.pred_real_aus = self.net_dis(self.src_img)
        self.loss_dis_real = self.criterionGAN(pred_real, True)
        self.loss_dis_real_aus = self.criterionMSE(self.pred_real_aus, self.src_aus)

        # fake image, detach to stop backward to generator
        pred_fake, _ = self.net_dis(self.fake_img.detach()) 
        self.loss_dis_fake = self.criterionGAN(pred_fake, False)

        # combine dis loss
        self.loss_dis =   self.opt.lambda_dis * (self.loss_dis_fake + self.loss_dis_real) \
                        + self.opt.lambda_aus * self.loss_dis_real_aus
        if self.opt.gan_type == 'wgan-gp':
            self.loss_dis_gp = self.gradient_penalty(self.src_img, self.fake_img)
            self.loss_dis = self.loss_dis + self.opt.lambda_wgan_gp * self.loss_dis_gp
        
        # backward discriminator loss
        self.loss_dis.backward(retain_graph=True)
    #------------------------------------    
    # new method for the generator
    #------------------------------------
    def backward_gen_pose(self):
        # original to target domain, should fake the discriminator
        pred_fake_pose, self.pred_fake_aus_pose = self.net_dis_pose(self.fake_img_pose)
        self.loss_gen_GAN_pose = self.criterionGAN(pred_fake_pose, True)
        self.loss_gen_fake_aus_pose = self.criterionMSE(self.pred_fake_aus_pose, self.tar_pose)

        # target to original domain reconstruct, identity loss
        self.loss_gen_rec_pose = self.criterionL1(self.rec_real_img_pose, self.fake_img_pose)

        # constrain on AUs mask
        self.loss_gen_mask_real_aus_pose = torch.mean(self.aus_mask_pose)
        self.loss_gen_mask_fake_aus_pose = torch.mean(self.rec_aus_mask_pose)
        self.loss_gen_smooth_real_aus_pose = self.criterionTV(self.aus_mask_pose)
        self.loss_gen_smooth_fake_aus_pose = self.criterionTV(self.rec_aus_mask_pose)

        # combine and backward G loss
        self.loss_gen_pose =   self.opt.lambda_dis * self.loss_gen_GAN_pose \
                        + self.opt.lambda_aus * self.loss_gen_fake_aus_pose \
                        + self.opt.lambda_rec * self.loss_gen_rec_pose \
                        + self.opt.lambda_mask * (self.loss_gen_mask_real_aus_pose + self.loss_gen_mask_fake_aus_pose) \
                        + self.opt.lambda_tv * (self.loss_gen_smooth_real_aus_pose + self.loss_gen_smooth_fake_aus_pose)

        self.loss_gen_pose.backward(retain_graph=True)

    def backward_gen(self):
        # original to target domain, should fake the discriminator
        pred_fake, self.pred_fake_aus = self.net_dis(self.fake_img)
        self.loss_gen_GAN = self.criterionGAN(pred_fake, True)
        self.loss_gen_fake_aus = self.criterionMSE(self.pred_fake_aus, self.tar_aus)

        # target to original domain reconstruct, identity loss
        self.loss_gen_rec = self.criterionL1(self.rec_real_img, self.src_img)

        # constrain on AUs mask
        self.loss_gen_mask_real_aus = torch.mean(self.aus_mask)
        self.loss_gen_mask_fake_aus = torch.mean(self.rec_aus_mask)
        self.loss_gen_smooth_real_aus = self.criterionTV(self.aus_mask)
        self.loss_gen_smooth_fake_aus = self.criterionTV(self.rec_aus_mask)

        # combine and backward G loss
        self.loss_gen =   self.opt.lambda_dis * self.loss_gen_GAN \
                        + self.opt.lambda_aus * self.loss_gen_fake_aus \
                        + self.opt.lambda_rec * self.loss_gen_rec \
                        + self.opt.lambda_mask * (self.loss_gen_mask_real_aus + self.loss_gen_mask_fake_aus) \
                        + self.opt.lambda_tv * (self.loss_gen_smooth_real_aus + self.loss_gen_smooth_fake_aus)

        self.loss_gen.backward(retain_graph=True)

    def optimize_paras(self, train_gen):
        self.forward()
        self.forward_pose()
        # update discriminator
        self.set_requires_grad_([self.net_dis, self.net_dis_pose], True)
        self.optim_dis.zero_grad()
        self.backward_dis()
        self.backward_dis_pose()
        self.optim_dis.step()

        # update G if needed
        if train_gen:
            self.set_requires_grad_([self.net_dis,self.net_dis_pose], False)
            self.optim_gen.zero_grad()
            self.backward_gen()
            self.backward_gen_pose()
            self.optim_gen.step()

    def save_ckpt(self, epoch):
        # save the specific networks
        save_models_name = ['gen','gen_pose', 'dis', 'dis_pose']
        return super(GANimationModel, self).save_ckpt(epoch, save_models_name)

    def load_ckpt(self, epoch):
        # load the specific part of networks
        load_models_name = ['gen','gen_pose']
        if self.is_train:
            load_models_name.extend(['dis'])
        return super(GANimationModel, self).load_ckpt(epoch, load_models_name)

    def clean_ckpt(self, epoch):
        # load the specific part of networks
        load_models_name = ['gen', 'dis', 'gen_pose', 'dis_pose']
        return super(GANimationModel, self).clean_ckpt(epoch, load_models_name)

    def get_latest_losses(self):
        get_losses_name = ['dis_fake', 'dis_real', 'dis_real_aus', 'gen_rec', 'dis_fake_pose', 'dis_real_pose', 'dis_real_aus_pose', 'gen_rec_pose']
        return super(GANimationModel, self).get_latest_losses(get_losses_name)

    def get_latest_visuals(self):
        visuals_name = ['src_img', 'tar_img', 'color_mask', 'aus_mask', 'fake_img', 'fake_img_pose', 'color_mask_pose', 'aus_mask_pose']
        if self.is_train:
            visuals_name.extend(['rec_color_mask', 'rec_aus_mask', 'rec_real_img'])
        return super(GANimationModel, self).get_latest_visuals(visuals_name)
