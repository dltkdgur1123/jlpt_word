[Streamlit 트레이 아이콘 없는 실행 패키지]

구성 파일
1. streamlit_background.pyw
   - Streamlit을 콘솔/작업 표시줄/시스템 트레이 아이콘 없이 실행합니다.
   - 실행된 프로세스 번호를 D:\backup\jlpt_word\streamlit_server.pid에 저장합니다.

2. start_streamlit_hidden.vbs
   - Windows 시작프로그램용 숨김 실행 파일입니다.

3. stop_streamlit_force.vbs
   - 저장된 PID를 이용해 해당 Streamlit 프로세스와 하위 프로세스를 강제 종료합니다.
   - 설치 후 바탕화면에 복사됩니다.

4. install_no_tray.bat
   - 위 파일을 자동 배치합니다.
   - 기존 시작프로그램의 run_streamlit_app.bat 및 run_streamlit_app_hidden.vbs를 제거합니다.

설치 방법
1. ZIP 파일의 압축을 풉니다.
2. install_no_tray.bat을 더블클릭합니다.
3. 설치가 끝나면 시작프로그램 폴더에 start_streamlit_hidden.vbs가 생성됩니다.
4. 바탕화면에는 stop_streamlit_force.vbs가 생성됩니다.
5. 재부팅하거나 start_streamlit_hidden.vbs를 더블클릭하여 실행을 확인합니다.

주의
- 프로젝트 경로는 D:\backup\jlpt_word 기준입니다.
- Streamlit 시작 파일은 streamlit_app.py 기준입니다.
- 강제 종료 후 다시 실행하려면 start_streamlit_hidden.vbs를 더블클릭하면 됩니다.
- 기존 streamlit_tray.py는 삭제하지 않아도 되지만, 시작프로그램에서 더 이상 실행되면 안 됩니다.
