wget https://s3.amazonaws.com/fast-ai-imageclas/imagenette2-320.tgz
gunzip imagenette2-320.tgz
tar -xvf imagenette2-320.tar

git clone https://github.com/PieterBlomme/pytorch-image-models
cd pytorch-image-models
source activate pytorch_p38
pip install -e .

python3 train.py ../imagenette2-320 --model resnet18 --epochs 2

export OUTPUTDIR="$(ls ./output/train | grep resnet)"
echo $OUTPUTDIR
python3 validate.py ../imagenette2-320/val --model resnet18 --checkpoint ./output/train/$OUTPUTDIR/model_best.pth.tar
