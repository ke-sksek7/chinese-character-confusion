import json
import torch
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix

from dataset import CharDataset
from model import resnet18_gray_64

DEVICE = torch.device("cpu")
NUM_CLASSES = 81
CHECKPOINT_PATH = "checkpoints_a/best_checkpoint.pt"

def main():
    # 加载 val_graph 集合，用于统计混淆（设计书6.4）
    ds_val_graph = CharDataset(split="val_graph")
    from torch.utils.data import DataLoader
    loader = DataLoader(ds_val_graph, batch_size=32, shuffle=False, num_workers=0)

    # 加载模型权重
    model = resnet18_gray_64(num_classes=NUM_CLASSES).to(DEVICE)
    ckpt = torch.load(CHECKPOINT_PATH, map_location=DEVICE, weights_only=False)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()
    print(f"载入checkpoint，epoch={ckpt['epoch']}, best_val_acc={ckpt['best_val_acc']:.4f}")

    all_labels = []
    all_preds = []
    all_logits = []

    with torch.no_grad():
        for imgs, labels in loader:
            imgs = imgs.to(DEVICE)
            labels = labels.to(DEVICE)
            logits = model(imgs)
            preds = torch.argmax(logits, dim=1)
            all_labels.extend(labels.cpu().numpy().tolist())
            all_preds.extend(preds.cpu().numpy().tolist())
            all_logits.append(logits.cpu())

    # 读取字符映射 class_id → 汉字
    with open("characters.json","r",encoding="utf-8") as f:
        char_info = json.load(f)
    id2char = {c["class_id"]: c["char"] for c in char_info["characters"]}

    # 计算混淆矩阵 N[i,j]：真实i，预测j
    cm = confusion_matrix(all_labels, all_preds, labels=list(range(NUM_CLASSES)))
    np.save("confusion_matrix.npy", cm)
    print("混淆矩阵已保存 confusion_matrix.npy")

    # 统计每个类别 top‑1 混淆目标 c(i)，过滤支持数>=5次
    confuse_records = []
    MIN_SUPPORT = 5
    for i in range(NUM_CLASSES):
        row = cm[i].copy()
        row[i] = -1  # 排除自身正确预测
        j = int(np.argmax(row))
        cnt = int(row[j])
        rec = {
            "class_id_true": i,
            "char_true": id2char[i],
            "class_id_confuse": j,
            "char_confuse": id2char[j],
            "count": cnt,
            "valid": cnt >= MIN_SUPPORT
        }
        confuse_records.append(rec)

    # 保存挖掘出来的混淆对，后面C/D组要用
    with open("confuse_pairs.json","w",encoding="utf-8") as f:
        json.dump(confuse_records, f, ensure_ascii=False, indent=2)
    print("挖掘混淆对保存 confuse_pairs.json")

    # 画混淆矩阵图；81类太多，文字标签会挤，只画色块，不打印全部汉字标签
    plt.figure(figsize=(12,11))
    plt.imshow(cm, cmap="Blues")
    plt.colorbar()
    plt.title(f"Confusion Matrix val_graph (81 chars)")
    plt.xlabel("predict class_id")
    plt.ylabel("true class_id")
    plt.tight_layout()
    plt.savefig("confusion_matrix.png", dpi=200)
    print("混淆矩阵图片保存 confusion_matrix.png")

    # 打印有足够样本的混淆对
    print("\n===== 满足最小支持>=5次的有向混淆对 =====")
    for r in confuse_records:
        if r["valid"]:
            print(f"{r['char_true']}({r['class_id_true']}) → {r['char_confuse']}({r['class_id_confuse']}), count={r['count']}")

if __name__ == "__main__":
    main()
