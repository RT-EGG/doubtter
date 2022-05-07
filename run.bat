@setlocal
@pushd %~dp0

call %~dp0env\Scripts\activate
python .\main.py
call deactivate

@popd
@endlocal

exit /b 0