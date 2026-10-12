import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torch.optim.lr_scheduler import CosineAnnealingLR
from pathlib import Path
import json

from dataset import CharDataset
from model import resnet18_gray_64

# =====================配置（和设计书v0.2对齐，CPU调试）=====================
DEVICE = torch.device("cpu")
NUM_CLASSES = 81
BATCH_SIZE = 64
EPOCHS = 30
LR = 0.001
WEIGHT_DECAY = 1e-4
SAVE_DIR = Path("checkpoints_a")
SAVE_DIR.mkdir(exist_ok=True)
# =========================================================================

def main():
    # 数据集与dataloader
    ds_train = CharDataset(split="train")
    ds_val_select = CharDataset(split="val_select")

    loader_train = DataLoader(ds_train, batch_size=BATCH_SIZE, shuffle=True, num_workers=0)
    loader_val = DataLoader(ds_val_select, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)

    print(f"train size: {len(ds_train)} | val_select size: {len(ds_val_select)}")

    # 模型、损失、优化器、学习率调度
    model = resnet18_gray_64(num_classes=NUM_CLASSES).to(DEVICE)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)
    scheduler = CosineAnnealingLR(optimizer, T_max=EPOCHS, eta_min=LR*0.01)

    log_records = []
    best_acc = 0.0

    for epoch in range(1, EPOCHS+1):
        # --------训练--------
        model.train()
        total_loss = 0.0
        correct_train = 0
        total_train = 0

        for imgs, labels in loader_train:
            imgs = imgs.to(DEVICE)
            labels = labels.to(DEVICE)

            optimizer.zero_grad()
            logits = model(imgs)
            loss = criterion(logits, labels)
            loss.backward()
            optimizer.step()

            total_loss += loss.item() * imgs.size(0)
            pred = torch.argmax(logits, dim=1)
            correct_train += torch.sum(pred == labels).item()
            total_train += imgs.size(0)

        train_loss = total_loss / total_train
        train_acc = correct_train / total_train

        # --------val_select验证（不更新权重）--------
        model.eval()
        correct_val = 0
        total_val = 0
        with torch.no_grad():
            for imgs, labels in loader_val:
                imgs = imgs.to(DEVICE)
                labels = labels.to(DEVICE)
                logits = model(imgs)
                pred = torch.argmax(logits, dim=1)
                correct_val += torch.sum(pred == labels).item()
                total_val += imgs.size(0)
        val_acc = correct_val / total_val

        scheduler.step()

        print(f"Epoch [{epoch:2d}/{EPOCHS}] "
              f"Train loss:{train_loss:.4f} | train_acc:{train_acc:.4f} "
              f"val_select_acc:{val_acc:.4f}")

        log_records.append({
            "epoch": epoch,
            "train_loss": round(train_loss,4),
            "train_acc": round(train_acc,4),
            "val_select_acc": round(val_acc,4),
            "lr": round(optimizer.param_groups[0]["lr"],6)
        })
        if val_acc >= 1.0:
            print(f"验证集准确率达到100%，触发早停，终止训练！")
            break
        # 保存最优checkpoint（按val_select准确率）
        if val_acc > best_acc:
            best_acc = val_acc
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "best_val_acc": best_acc
            }, SAVE_DIR / "best_checkpoint.pt")
            print(f"--> 保存最优模型 epoch{epoch}, val_acc={best_acc:.4f}")

    # 保存训练日志
    with open(SAVE_DIR / "log.json","w",encoding="utf-8") as f:
        json.dump(log_records, f, indent=2, ensure_ascii=False)

    print(f"\n训练结束，最优val_select acc: {best_acc:.4f}")
    print(f"checkpoint保存在 {SAVE_DIR.resolve()}")

if __name__ == "__main__":
    main()
