# Bitqik QR Studio · ລະບົບສ້າງ ແລະ ຕິດຕາມການ Scan QR Code (QR Tracking WebApp)

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/Menh-d/-bitqik-qr_Tracking)

ລະບົບ Web Application ສໍາລັບສ້າງ QR Code ຕິດແບຣນ **Bitqik** (ໂລໂກ້ Bitqik ໃຈກາງ, ສີສັນ Neumorphic Warm Orange & Navy) ພ້ອມລະບົບ **Dynamic Redirect & Real-time Scan Tracking** ຕິດຕາມສະຖິຕິການ Scan ຜ່ານກ້ອງມືຖືແທ້ໆ!

---

## 🌟 ຄຸນສົມບັດຫຼັກ (Key Features)

1. **Dynamic Tracked QR Code (ຕິດຕາມການ Scan ແທ້ໆ)**:
   - ທຸກໆ QR Code ທີ່ສ້າງແບບ Dynamic ຈະມີ Short Link ເຊັ່ນ: `http://<IP>:8000/r/<short_code>`
   - ເມື່ອມີຄົນໃຊ້ກ້ອງມືຖືສະແກນ:
     - ລະບົບ Server ຈະບັນທຶກ: **ວັນທີ-ເວລາ, ປະເພດອຸປະກອນ (iOS / Android / Desktop), Browser (Safari / Chrome / Facebook / TikTok / Line), IP Address, ແລະ ແຫຼ່ງທີ່ມາ**
     - ແລ້ວ **Redirect (HTTP 302)** ໄປຫາ Destination URL (ເຊັ່ນ: `https://bitqik.com/download` ຫຼື ໜ້າ Campaign) ທັນທີ!
2. **ປ່ຽນ Destination URL ໄດ້ຕະຫຼອດເວລາ (Dynamic)**:
   - ຫາກພິມ QR Code ຕິດໃສ່ Standee, ໃບປິວ, ເສື້ອ ຫຼື ປ້າຍໂຄສະນາແລ້ວ ຢາກປ່ຽນລິ້ງປາຍທາງ ບໍ່ຈໍາເປັນຕ້ອງພິມ QR ໃໝ່! ພຽງແຕ່ກົດ "Edit URL" ໃນ Dashboard ແລ້ວບັນທຶກ QR ເດີມຈະສົ່ງໄປລິ້ງໃໝ່ທັນທີ.
3. **Analytics Dashboard ແບບ Real-time**:
   - ບັດສະຖິຕິ: ຈຳນວນ QR ທັງໝົດ, ຈຳນວນຄັ້ງທີ່ Scan, Scan ມື້ນີ້, ສະເລ່ຍຕໍ່ QR.
   - **Chart.js Bar Chart**: ແຄມເປນທີ່ຖືກ Scan ຫຼາຍທີ່ສຸດ (Top Campaigns).
   - **Chart.js Doughnut Chart**: ສັດສ່ວນອຸປະກອນທີ່ໃຊ້ Scan (iPhone vs Android vs PC).
   - **Live Activity Feed**: ສະແດງປະຫວັດການ Scan ລ່າສຸດແບບ Real-time ອັດຕະໂນມັດທຸກ 5 ວິນາທີ.
4. **Custom Branded QR Generator**:
   - ຕິດໂລໂກ້ Bitqik ຢູ່ໃຈກາງ (Vector High-Res) ຫຼື Upload ໂລໂກ້ຂອງຕົນເອງ.
   - ດາວໂຫລດໄຟລ໌ **SVG (Vector)** ສຳລັບງານພິມຂະໜາດໃຫຍ່ (Standee, Billboard, ເສື້ອ).
   - ດາວໂຫລດ **PNG (HD 1200x1200px)**.
   - ປຸ່ມ **Print Card**: ສ້າງໃບຕັ້ງໂຕະ/ປ້າຍ Scan ພ້ອມພິມ (Print Standee Card).
5. **In-App Camera & Image QR Scanner (ທົດສອບສະແກນໃນຕົວ)**:
   - ມີປຸ່ມ "ທົດສອບ Scan" ທີ່ເປີດກ້ອງ Webcam/ມືຖື ຫຼື Upload ຮູບ QR Code ເພື່ອທົດສອບການ Scan ໄດ້ທັນທີ.
6. **Export Data**:
   - ດາວໂຫລດລາຍງານສະຖິຕິການ Scan ທັງໝົດອອກເປັນ **CSV / Excel** ໄດ້ທັນທີ.
7. **Bilingual Interface**:
   - ຮອງຮັບທັງ **ພາສາລາວ (LA)** ແລະ **English (EN)** ພຽງແຕ່ກົດປຸ່ມ Toggle ຢູ່ມຸມຂວາເທິງ.

---

## 🚀 ວິທີການເປີດໃຊ້ງານ (How to Run)

### ວິທີທີ 1: ເປີດຜ່ານ Terminal (ແນະນຳ ສຳລັບການ Track ແທ້ໆ)

1. ເປີດ Terminal ແລ້ວເຂົ້າໄປທີ່ໂຟນເດີໂປຣເຈັກ:
   ```bash
   cd "/Users/graphic/Documents/antigravity/bitqik"
   ```
2. ສັ່ງ Run Server (ໃຊ້ Python ມາດຕະຖານ ບໍ່ຕ້ອງລົງ Library ເພີ່ມ):
   ```bash
   ./start.sh
   # ຫຼື: python3 server.py 8000
   ```
3. ເປີດ Web Browser ໄປທີ່:
   - ໃນຄອມພິວເຕີ: `http://localhost:8000`
   - **ສຳລັບມືຖື**: ເປີດ Safari/Chrome ໃນມືຖືທີ່ຕໍ່ Wi-Fi ດຽວກັນ ແລ້ວພິມ IP ທີ່ Server ສະແດງ (ເຊັ່ນ `http://192.168.1.xxx:8000`)

---

### ວິທີທີ 2: ເປີດໄຟລ໌ HTML ໂດຍກົງ (Standalone Mode)

ຫາກຍັງບໍ່ທັນເປີດ Server, ທ່ານສາມາດ Double-click ເປີດໄຟລ໌:
- `/Users/graphic/Documents/Work/bitqik QR Tracked.html`
- ຫຼື `/Users/graphic/Documents/antigravity/bitqik/index.html`

ລະບົບຈະເຮັດວຽກໃນຮູບແບບ **Standalone Mode** ຜ່ານ `localStorage` ໃຫ້ທັນທີ ສາມາດສ້າງ QR, ດາວໂຫລດ, ແລະ ທົດສອບການ Scan ໄດ້ຄົບຖ້ວນ!

---

## 📁 ໂຄງສ້າງໄຟລ໌ (Project Structure)

- `server.py`: Python Multi-threaded HTTP Server + REST API + 302 Dynamic Tracking Redirect + LAN IP Auto-detection.
- `database.py`: SQLite Database Handler (ເກັບຂໍ້ມູນ QR Codes ແລະ Scan Logs ຢ່າງປອດໄພ ບໍ່ສູນຫາຍ).
- `index.html`: ໜ້າ Web Application ຫຼັກ (Soft-UI Neumorphic Bitqik Theme, Lao/English, Charts, Scanner).
- `start.sh`: Shell script ສຳລັບ Start Server ດ້ວຍຄລິກດຽວ.
- `/Users/graphic/Documents/Work/bitqik QR Tracked.html`: ໄຟລ໌ຕົ້ນສະບັບທີ່ຖືກອັບເດດແກ້ໄຂໃຫ້ສົມບູນ 100%.
- `bitqik_qr.db`: ຖານຂໍ້ມູນ SQLite ທີ່ບັນທຶກແຄມເປນ ແລະ ປະຫວັດການ Scan.
