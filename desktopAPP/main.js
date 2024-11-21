/* 
const { app, BrowserWindow } = require('electron/main');
const path = require('node:path');
require('dotenv').config(); // .env 파일에서 환경 변수 로드

const createWindow = () => {
  // 환경 변수에서 SLACK_BOT_TOKEN 값 확인
  const slackBotToken = process.env.SLACK_BOT_TOKEN;

  const win = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
    },
  });

  // 조건에 따라 로드할 파일 결정
  // 해당 화면은 환경변수나 저장경로등을 아예 설정하지 않은 경우나 설정한 경우에 따라
  // 바로 홈화면으로 갈지 입력창을 띄울지 확인하는 GUI  
  if (slackBotToken) {
    win.loadFile('index.html'); // SLACK_BOT_TOKEN이 존재하면 index.html 로드
  } else {
    win.loadFile('input.html'); // SLACK_BOT_TOKEN이 없으면 input.html 로드
  }
};

app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
*/
/*
const { app, BrowserWindow, ipcMain } = require('electron/main');
const path = require('node:path');
const { execSync, exec } = require('child_process');
require('dotenv').config();

const checkDependencies = () => {
  let dependenciesMissing = [];

  // Node.js 확인
  try {
    execSync('node -v');
  } catch (error) {
    dependenciesMissing.push('Node.js');
  }

  // npm 확인
  try {
    execSync('npm -v');
  } catch (error) {
    dependenciesMissing.push('npm');
  }

  // Python 확인
  try {
    execSync('python --version');
  } catch (error) {
    dependenciesMissing.push('Python');
  }

  return dependenciesMissing;
};

const installDependencies = (win, dependencies) => {
  const packages = {
    'Node.js': 'nodejs',
    'npm': 'nodejs',
    'Python': 'python'
  };

  dependencies.forEach(dep => {
    if (packages[dep]) {
      exec(`choco install ${packages[dep]} -y`, (error, stdout, stderr) => {
        const status = error ? `${dep} 설치 실패: ${stderr}` : `${dep} 설치 완료`;
        console.log(status);
        win.webContents.send('install-status', status);
      });
    }
  });
};

const createWindow = () => {
  const missingDependencies = checkDependencies();
  const win = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: true,
      contextIsolation: false
    },
  });

  // check_package.html 로드
  win.loadFile('check_package.html');

  // IPC 이벤트 처리: 다음으로 버튼 클릭 시 install.html 로드 및 설치 시작
  ipcMain.on('go-to-install', () => {
    win.loadFile('install.html');
    installDependencies(win, missingDependencies);
  });

  // 누락된 패키지 목록 전송
  win.webContents.on('did-finish-load', () => {
    win.webContents.send('missing-dependencies', missingDependencies);
  });
};

app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});*/
/* 
const { app, BrowserWindow, ipcMain } = require('electron/main');
const path = require('node:path');
const { execSync, exec, spawn } = require('child_process');
require('dotenv').config();
const fs = require('fs');

let flaskProcess = null;
let localtunnelProcess = null;

const checkDependencies = () => {
  let dependenciesMissing = [];

  // Node.js 확인
  try {
    execSync('node -v');
  } catch (error) {
    dependenciesMissing.push('Node.js');
  }

  // npm 확인
  try {
    execSync('npm -v');
  } catch (error) {
    dependenciesMissing.push('npm');
  }

  // Python 확인
  try {
    execSync('python --version');
  } catch (error) {
    dependenciesMissing.push('Python');
  }

  // Chocolatey 확인
  try {
    execSync('choco -v');
  } catch (error) {
    dependenciesMissing.push('Chocolatey');
  }

// Check if localtunnel is installed (global)
try {
  let result = execSync('npm list -g --depth=0 | findstr localtunnel', { encoding: 'utf-8' });
  if (!result.includes('localtunnel')) {
    dependenciesMissing.push('localtunnel');
  }
} catch (error) {
  dependenciesMissing.push('localtunnel');
}

// Check if dotenv is installed (local)
try {
  let result = execSync('npm list --depth=0 | findstr dotenv', { encoding: 'utf-8' });
  if (!result.includes('dotenv')) {
    dependenciesMissing.push('dotenv');
  }
} catch (error) {
  dependenciesMissing.push('dotenv');
}

  if (fs.existsSync('requirements.txt')) {
    try {
      // pip install --dry-run to simulate the installation check
      execSync('pip install -r requirements.txt --dry-run');
    } catch (error) {
      dependenciesMissing.push('requirements');
    }
  } else {
    dependenciesMissing.push('requirements.txt file is missing.');
  }

  return dependenciesMissing;
};

const setExecutionPolicy = () => {
  try {
    execSync('Set-ExecutionPolicy Bypass -Scope Process -Force', { shell: 'powershell.exe', stdio: 'inherit' });
    console.log('Execution policy set to Bypass');
  } catch (error) {
    console.error('Failed to set execution policy:', error);
  }
};

const installDependencies = (win, dependencies) => {
  if (dependencies.length === 0) {
    // 설치할 것이 없으면 바로 추가 패키지 설치 호출
    installAdditionalPackages(win);
    return;
  }

  const packages = {
    'Node.js': 'nodejs',
    'npm': 'nodejs',
    'Python': 'python',
    'Chocolatey': 'choco'
  };

  // Chocolatey가 목록에 있는 경우 먼저 동기적으로 설치
  if (dependencies.includes('Chocolatey')) {
    try {
      win.webContents.send('install-status', 'Chocolatey 설치 중...');
      const installScript = `
        Set-ExecutionPolicy Bypass -Scope Process -Force;
        [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072;
        iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
      `;
      execSync(installScript, { stdio: 'inherit' });
      win.webContents.send('install-status', 'Chocolatey 설치 완료');
      console.log('Chocolatey 설치 완료');
      dependencies = dependencies.filter(dep => dep !== 'Chocolatey'); // 목록에서 제거
    } catch (error) {
      console.error('Chocolatey 설치에 실패했습니다:', error);
      win.webContents.send('install-status', 'Chocolatey 설치 실패');
      return; // 실패 시 나머지 진행하지 않음
    }
  }

  // 나머지 의존성 동기적으로 설치
  dependencies.forEach(dep => {
    if (packages[dep]) {
      try {
        win.webContents.send('install-status', `${dep} 설치 중...`);
        execSync(`choco install ${packages[dep]} -y`, { stdio: 'inherit' });
        const status = `${dep} 설치 완료`;
        console.log(status);
        win.webContents.send('install-status', status);
      } catch (error) {
        const status = `${dep} 설치 실패: ${error.message}`;
        console.error(status);
        win.webContents.send('install-status', status);
      }
    }
  });

  // 모든 설치 완료 후 추가 패키지 설치 호출
  installAdditionalPackages(win, dependencies);
};

const installAdditionalPackages = (win, dependenciesMissing) => {
  // 필요한 추가 패키지 목록만 필터링
  const additionalPackages = dependenciesMissing.filter(dep => 
  dep === 'localtunnel' || 
  dep === 'dotenv' || 
  dep === 'requirements');
  let installationsCompleted = 0;
  const totalInstallations = additionalPackages.length;

  const checkAllInstallationsCompleted = () => {
    if (installationsCompleted === totalInstallations) {
      console.log('All additional packages installed. Sending "all-installed" signal.');
      win.webContents.send('all-installed'); // 모든 설치 완료 시 메시지 전송
    }
  };

  // Python requirements.txt 설치
  if (dependenciesMissing.includes('requirements')) {
    win.webContents.send('install-status', 'requirements.txt 설치 중...');
    console.log('Installing Python dependencies from requirements.txt...');
    try {
      execSync('pip install -r requirements.txt', { stdio: 'inherit' }); // 재설치 진행
      console.log('Python dependencies installed from requirements.txt.');
      win.webContents.send('install-status', 'requirements.txt 설치 완료');
      installationsCompleted += 1;
      checkAllInstallationsCompleted(); // 설치 완료 여부 확인
    } catch (error) {
      console.error('Failed to install Python dependencies:', error);
      win.webContents.send('install-status', `requirements.txt 설치 실패: ${error.message}`);
      installationsCompleted += 1; // 실패해도 카운터 증가
      checkAllInstallationsCompleted();
    }
  }

  // localtunnel 전역 설치
  if (dependenciesMissing.includes('localtunnel')) {
    win.webContents.send('install-status', 'localtunnel 전역 설치 중...');
    console.log('Installing localtunnel globally...');
    try {
      execSync('npm install -g localtunnel', { stdio: 'inherit' }); // 전역 설치
      console.log('localtunnel installed globally.');
      win.webContents.send('install-status', 'localtunnel 전역 설치 완료');
    } catch (error) {
      console.error('Failed to install localtunnel globally:', error);
      win.webContents.send('install-status', `localtunnel 전역 설치 실패: ${error.message}`);
    } finally {
      installationsCompleted += 1; // 성공 또는 실패 여부에 상관없이 카운터 증가
      checkAllInstallationsCompleted();
    }
  }

  // dotenv 지역 설치
  if (dependenciesMissing.includes('dotenv')) {
    win.webContents.send('install-status', 'dotenv 지역 설치 중...');
    console.log('Installing dotenv locally...');
    try {
      execSync('npm install dotenv', { stdio: 'inherit' }); // 지역 설치
      console.log('dotenv installed locally.');
      win.webContents.send('install-status', 'dotenv 지역 설치 완료');
    } catch (error) {
      console.error('Failed to install dotenv locally:', error);
      win.webContents.send('install-status', `dotenv 지역 설치 실패: ${error.message}`);
    } finally {
      installationsCompleted += 1; // 성공 또는 실패 여부에 상관없이 카운터 증가
      checkAllInstallationsCompleted();
    }
  }
};



const createWindow = () => {
  setExecutionPolicy(); // 처음 실행 시 스크립트 실행 권한 설정
  const missingDependencies = checkDependencies();
  const win = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: true,
      contextIsolation: false
    },
  });

  // check_package.html 로드
  win.loadFile('check_package.html');

  // check_package.html이 로드된 후 go-to-install-or-next 이벤트 트리거
  win.webContents.on('did-finish-load', () => {
    ipcMain.emit('go-to-install-or-next');
  });

  // 필요한 의존성이 모두 설치되어 있는 경우 input.html로 이동
  ipcMain.on('go-to-install-or-next', () => {
    if (missingDependencies.length === 0) {
      // 의존성이 모두 설치되었으므로, 환경 변수 상태에 따라 이동
      win.webContents.on('did-finish-load', () => {
        ipcMain.emit('go-to-input-or-index');
      });
    } else {
      // 필요한 의존성이 누락된 경우 install.html 로 이동 및 설치 시작
      win.loadFile('install.html');
      win.webContents.on('did-finish-load', () => {
        installDependencies(win, missingDependencies);
      });
    }
  });

  // IPC 이벤트 처리: 다음으로 버튼 클릭 시 install.html 로드 및 설치 시작
  ipcMain.on('go-to-install', () => {
    win.loadFile('install.html');

    // install.html이 로드된 후에 설치 시작
    win.webContents.on('did-finish-load', () => {
      installDependencies(win, missingDependencies);
    });
  });

  // IPC 이벤트 처리: 다음으로 버튼 클릭 시 input.html 또는 index.html로 이동
  ipcMain.on('go-to-input-or-index', () => {
    const slackBotToken = process.env.SLACK_BOT_TOKEN;
    const botSubdomain = process.env.BOT_SUBDOMAIN;
    if (slackBotToken && botSubdomain) {
      win.loadFile('index.html'); // 두 환경 변수가 모두 존재하면 index.html 로드
    } else {
      win.loadFile('input.html'); // 둘 중 하나라도 없으면 input.html 로드
    }
  });

  ipcMain.on('request-credentials', (event) => {
    const slackBotToken = process.env.SLACK_BOT_TOKEN || '';
    const botSubdomain = process.env.BOT_SUBDOMAIN || '';
      event.sender.send('load-credentials', { token: slackBotToken, subdomain: botSubdomain });
  });
    
  ipcMain.on('set-credentials', (event, token, subdomain) => {
    const dotenvFilePath = path.join(__dirname, '.env');
    fs.appendFileSync(dotenvFilePath, `SLACK_BOT_TOKEN=${token}\n`);
    fs.appendFileSync(dotenvFilePath, `BOT_SUBDOMAIN=${subdomain}\n`);
    process.env.SLACK_BOT_TOKEN = token; // 환경 변수 즉시 반영
    process.env.BOT_SUBDOMAIN = subdomain;
    event.sender.send('credentials-saved');  
  });
    
    ipcMain.on('start-bot', () => {
    // Flask 서버 시작
    if (!flaskProcess) {
        const pythonCommand = 'python'; // Windows에서 python 또는 python3 확인 필요
        const slackScriptPath = path.join(__dirname, 'slack_test.py');
        console.log(__dirname); // 현재 스크립트의 디렉토리 경로가 출력됩니다.
        console.log(slackScriptPath); // slack_test.py에 대한 절대 경로가 출력됩니다.
        flaskProcess = spawn(pythonCommand, [slackScriptPath], { shell: true });

        flaskProcess.stdout.on('data', (data) => {
            console.log(`Flask stdout: ${data}`);
        });

        flaskProcess.stderr.on('data', (data) => {
            console.error(`Flask stderr: ${data}`);
        });

        flaskProcess.on('close', (code) => {
            console.log(`Flask process exited with code ${code}`);
            flaskProcess = null;
        });

        console.log('Flask server started.');
    } else {
        console.log('Flask server is already running.');
    }

    // 로컬터널 시작
    if (!localtunnelProcess) {
        const subdomain = process.env.BOT_SUBDOMAIN || 'default-subdomain';
        localtunnelProcess = spawn('lt', ['--port', '5000', '--subdomain', subdomain], { shell: true });

        localtunnelProcess.stdout.on('data', (data) => {
            console.log(`Localtunnel stdout: ${data}`);
        });

        localtunnelProcess.stderr.on('data', (data) => {
            console.error(`Localtunnel stderr: ${data}`);
        });

        localtunnelProcess.on('close', (code) => {
            console.log(`Localtunnel process exited with code ${code}`);
            localtunnelProcess = null;
        });

        console.log('Localtunnel started.');
    } else {
        console.log('Localtunnel is already running.');
    }
});

ipcMain.on('stop-bot', () => {
    // Flask 서버 종료
    if (flaskProcess) {
        console.log('Stopping Flask server...');
        flaskProcess.kill();
        flaskProcess = null;
    } else {
        console.log('No Flask server to stop.');
    }

    // 로컬터널 종료
    if (localtunnelProcess) {
        console.log('Stopping localtunnel...');
        localtunnelProcess.kill();
        localtunnelProcess = null;
    } else {
        console.log('No localtunnel process to stop.');
    }
});
    
  // 누락된 패키지 목록 전송
  win.webContents.on('did-finish-load', () => {
    win.webContents.send('missing-dependencies', missingDependencies);
  });
};

app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

// 앱 종료 시 모든 프로세스 정리
app.on('window-all-closed', () => {
    if (flaskProcess) {
        flaskProcess.kill();
    }
    if (localtunnelProcess) {
        localtunnelProcess.kill();
    }
    if (process.platform !== 'darwin') {
        app.quit();
    }
});
*/
/* 
const { app, BrowserWindow, ipcMain } = require('electron/main');
const path = require('node:path');
const { execSync, exec, spawn } = require('child_process');
require('dotenv').config();
const fs = require('fs');

let flaskProcess = null;
let localtunnelProcess = null;

const checkDependencies = () => {
  let dependenciesMissing = [];

  // Node.js 확인
  try {
    execSync('node -v');
  } catch (error) {
    dependenciesMissing.push('Node.js');
  }

  // npm 확인
  try {
    execSync('npm -v');
  } catch (error) {
    dependenciesMissing.push('npm');
  }

  // Python 확인
  try {
    execSync('python --version');
  } catch (error) {
    dependenciesMissing.push('Python');
  }

  // Chocolatey 확인
  try {
    execSync('choco -v');
  } catch (error) {
    dependenciesMissing.push('Chocolatey');
  }

  return dependenciesMissing;
};

const setExecutionPolicy = () => {
  try {
    execSync('Set-ExecutionPolicy Bypass -Scope Process -Force', { shell: 'powershell.exe', stdio: 'inherit' });
    console.log('Execution policy set to Bypass');
  } catch (error) {
    console.error('Failed to set execution policy:', error);
  }
};

const installDependencies = (win, dependencies) => {
  if (dependencies.length === 0) {
    // 설치할 것이 없으면 바로 추가 패키지 설치 호출
    installAdditionalPackages(win);
    return;
  }

  const packages = {
    'Node.js': 'nodejs',
    'npm': 'nodejs',
    'Python': 'python',
    'Chocolatey': 'choco'
  };

  // Chocolatey가 목록에 있는 경우 먼저 동기적으로 설치
  if (dependencies.includes('Chocolatey')) {
    try {
      win.webContents.send('install-status', 'Chocolatey 설치 중...');
      const installScript = `
        Set-ExecutionPolicy Bypass -Scope Process -Force;
        [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072;
        iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
      `;
      execSync(installScript, { stdio: 'inherit' });
      win.webContents.send('install-status', 'Chocolatey 설치 완료');
      console.log('Chocolatey 설치 완료');
      dependencies = dependencies.filter(dep => dep !== 'Chocolatey'); // 목록에서 제거
    } catch (error) {
      console.error('Chocolatey 설치에 실패했습니다:', error);
      win.webContents.send('install-status', 'Chocolatey 설치 실패');
      return; // 실패 시 나머지 진행하지 않음
    }
  }

  // 나머지 의존성 동기적으로 설치
  dependencies.forEach(dep => {
    if (packages[dep]) {
      try {
        win.webContents.send('install-status', `${dep} 설치 중...`);
        execSync(`choco install ${packages[dep]} -y`, { stdio: 'inherit' });
        const status = `${dep} 설치 완료`;
        console.log(status);
        win.webContents.send('install-status', status);
      } catch (error) {
        const status = `${dep} 설치 실패: ${error.message}`;
        console.error(status);
        win.webContents.send('install-status', status);
      }
    }
  });

  // 모든 설치 완료 후 추가 패키지 설치 호출
  installAdditionalPackages(win);
};

const installAdditionalPackages = (win) => {
  let installationsCompleted = 0; // 설치 완료 카운터
  const totalInstallations = 3; // 총 설치할 작업 수 (requirements.txt + localtunnel + dotenv)

  const checkAllInstallationsCompleted = () => {
    if (installationsCompleted === totalInstallations) {
      console.log('All additional packages installed. Sending "all-installed" signal.');
      win.webContents.send('all-installed'); // 모든 설치 완료 시 메시지 전송
    }
  };

  // Python requirements.txt 설치
  if (fs.existsSync('requirements.txt')) {
    win.webContents.send('install-status', 'requirements.txt 설치 중...');
    console.log('Installing Python dependencies from requirements.txt...');
    exec('pip install -r requirements.txt', (error, stdout, stderr) => {
      if (error) {
        console.error(`Failed to install Python dependencies: ${error}`);
        win.webContents.send('install-status', `requirements.txt 설치 실패: ${error.message}`);
      } else {
        console.log('Python dependencies installed from requirements.txt.');
        win.webContents.send('install-status', 'requirements.txt 설치 완료');
      }
      installationsCompleted += 1;
      checkAllInstallationsCompleted(); // 설치 완료 여부 확인
    });
  } else {
    console.log('No requirements.txt found.');
    win.webContents.send('install-status', 'requirements.txt가 없습니다.');
    installationsCompleted += 1;
    checkAllInstallationsCompleted();
  }

  // npm localtunnel 설치
  win.webContents.send('install-status', 'localtunnel 설치 중...');
  console.log('Installing localtunnel using npm...');
  exec('npm install -g localtunnel', (error, stdout, stderr) => {
    if (error) {
      console.error(`Failed to install localtunnel: ${error}`);
      win.webContents.send('install-status', `localtunnel 설치 실패: ${error.message}`);
    } else {
      console.log('localtunnel installed.');
      win.webContents.send('install-status', 'localtunnel 설치 완료');
    }
    installationsCompleted += 1;
    checkAllInstallationsCompleted(); // 설치 완료 여부 확인
  });

  // npm dotenv 설치
  win.webContents.send('install-status', 'dotenv 설치 중...');
  console.log('Installing dotenv using npm...');
  exec('npm install dotenv', (error, stdout, stderr) => {
    if (error) {
      console.error(`Failed to install dotenv: ${error}`);
      win.webContents.send('install-status', `dotenv 설치 실패: ${error.message}`);
    } else {
      console.log('dotenv installed.');
      win.webContents.send('install-status', 'dotenv 설치 완료');
    }
    installationsCompleted += 1;
    checkAllInstallationsCompleted(); // 설치 완료 여부 확인
  });
};


const createWindow = () => {
  setExecutionPolicy(); // 처음 실행 시 스크립트 실행 권한 설정
  const missingDependencies = checkDependencies();
  const win = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: true,
      contextIsolation: false
    },
  });

  // check_package.html 로드
  win.loadFile('check_package.html');

  // IPC 이벤트 처리: 다음으로 버튼 클릭 시 install.html 로드 및 설치 시작
  ipcMain.on('go-to-install', () => {
    win.loadFile('install.html');

    // install.html이 로드된 후에 설치 시작
    win.webContents.on('did-finish-load', () => {
      installDependencies(win, missingDependencies);
    });
  });

  // IPC 이벤트 처리: 다음으로 버튼 클릭 시 input.html 또는 index.html로 이동
  ipcMain.on('go-to-input-or-index', () => {
    const slackBotToken = process.env.SLACK_BOT_TOKEN;
    const botSubdomain = process.env.BOT_SUBDOMAIN;
    if (slackBotToken && botSubdomain) {
      win.loadFile('index.html'); // 두 환경 변수가 모두 존재하면 index.html 로드
    } else {
      win.loadFile('input.html'); // 둘 중 하나라도 없으면 input.html 로드
    }
  });

  ipcMain.on('request-credentials', (event) => {
    const slackBotToken = process.env.SLACK_BOT_TOKEN || '';
    const botSubdomain = process.env.BOT_SUBDOMAIN || '';
      event.sender.send('load-credentials', { token: slackBotToken, subdomain: botSubdomain });
  });
    
  ipcMain.on('set-credentials', (event, token, subdomain) => {
    const dotenvFilePath = path.join(__dirname, '.env');
    fs.appendFileSync(dotenvFilePath, `SLACK_BOT_TOKEN=${token}\n`);
    fs.appendFileSync(dotenvFilePath, `BOT_SUBDOMAIN=${subdomain}\n`);
    process.env.SLACK_BOT_TOKEN = token; // 환경 변수 즉시 반영
    process.env.BOT_SUBDOMAIN = subdomain;
    event.sender.send('credentials-saved');  
  });
    
    ipcMain.on('start-bot', () => {
    // Flask 서버 시작
    if (!flaskProcess) {
        const pythonCommand = 'python'; // Windows에서 python 또는 python3 확인 필요
        const slackScriptPath = path.join(__dirname, 'slack_test.py');
        console.log(__dirname); // 현재 스크립트의 디렉토리 경로가 출력됩니다.
        console.log(slackScriptPath); // slack_test.py에 대한 절대 경로가 출력됩니다.
        flaskProcess = spawn(pythonCommand, [slackScriptPath], { shell: true });

        flaskProcess.stdout.on('data', (data) => {
            console.log(`Flask stdout: ${data}`);
        });

        flaskProcess.stderr.on('data', (data) => {
            console.error(`Flask stderr: ${data}`);
        });

        flaskProcess.on('close', (code) => {
            console.log(`Flask process exited with code ${code}`);
            flaskProcess = null;
        });

        console.log('Flask server started.');
    } else {
        console.log('Flask server is already running.');
    }

    // 로컬터널 시작
    if (!localtunnelProcess) {
        const subdomain = process.env.BOT_SUBDOMAIN || 'default-subdomain';
        localtunnelProcess = spawn('lt', ['--port', '5000', '--subdomain', subdomain], { shell: true });

        localtunnelProcess.stdout.on('data', (data) => {
            console.log(`Localtunnel stdout: ${data}`);
        });

        localtunnelProcess.stderr.on('data', (data) => {
            console.error(`Localtunnel stderr: ${data}`);
        });

        localtunnelProcess.on('close', (code) => {
            console.log(`Localtunnel process exited with code ${code}`);
            localtunnelProcess = null;
        });

        console.log('Localtunnel started.');
    } else {
        console.log('Localtunnel is already running.');
    }
});

ipcMain.on('stop-bot', () => {
    // Flask 서버 종료
    if (flaskProcess) {
        console.log('Stopping Flask server...');
        flaskProcess.kill();
        flaskProcess = null;
    } else {
        console.log('No Flask server to stop.');
    }

    // 로컬터널 종료
    if (localtunnelProcess) {
        console.log('Stopping localtunnel...');
        localtunnelProcess.kill();
        localtunnelProcess = null;
    } else {
        console.log('No localtunnel process to stop.');
    }
});
    
  // 누락된 패키지 목록 전송
  win.webContents.on('did-finish-load', () => {
    win.webContents.send('missing-dependencies', missingDependencies);
  });
};

app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

// 앱 종료 시 모든 프로세스 정리
app.on('window-all-closed', () => {
    if (flaskProcess) {
        flaskProcess.kill();
    }
    if (localtunnelProcess) {
        localtunnelProcess.kill();
    }
    if (process.platform !== 'darwin') {
        app.quit();
    }
});
*/
const { app, BrowserWindow, ipcMain } = require('electron/main');
const path = require('node:path');
const { execSync, exec, spawn } = require('child_process');
/*require('dotenv').config();*/
const fs = require('fs');

// dotenv 로딩을 시도하고, 실패하면 무시합니다.
try {
  require('dotenv').config();
} catch (error) {
  console.log('dotenv not found, skipping environment variable loading from .env file');
}

let flaskProcess = null;
let localtunnelProcess = null;

const checkDependencies = () => {
  let dependenciesMissing = [];

  // Node.js 확인
  try {
    execSync('node -v');
  } catch (error) {
    dependenciesMissing.push('Node.js');
  }

  // npm 확인
  try {
    execSync('npm -v');
  } catch (error) {
    dependenciesMissing.push('npm');
  }

  // Python 확인
  try {
    execSync('python --version');
  } catch (error) {
    dependenciesMissing.push('Python');
  }

  // Chocolatey 확인
  try {
    execSync('choco -v');
  } catch (error) {
    dependenciesMissing.push('Chocolatey');
  }

  // Check if localtunnel is installed (global)
try {
  console.log('Checking if localtunnel is installed globally...');
  let result = execSync('npm list -g --depth=0 | findstr localtunnel', { encoding: 'utf-8' });
  if (!result.includes('localtunnel')) {
    console.log('localtunnel is not installed globally.');
    dependenciesMissing.push('localtunnel');
  } else {
    console.log('localtunnel is installed globally.');
  }
} catch (error) {
  console.log('Error checking for global localtunnel installation:', error);
  dependenciesMissing.push('localtunnel');
}

// Check if dotenv is installed (local)
try {
  console.log('Checking if dotenv is installed locally...');
  let result = execSync('npm list --depth=0 | findstr dotenv', { encoding: 'utf-8' });
  if (!result.includes('dotenv')) {
    console.log('dotenv is not installed locally.');
    dependenciesMissing.push('dotenv');
  } else {
    console.log('dotenv is installed locally.');
  }
} catch (error) {
  console.log('Error checking for local dotenv installation:', error);
  dependenciesMissing.push('dotenv');
}

// Check for requirements.txt and simulate installation check
if (fs.existsSync('requirements.txt')) {
  console.log('requirements.txt found, checking for necessary installations...');
  try {
    // pip install --dry-run to simulate the installation check
    execSync('pip install -r requirements.txt --dry-run');
    console.log('requirements.txt dependencies are valid or already installed.');
  } catch (error) {
    console.log('Error with requirements.txt simulation installation:', error);
    dependenciesMissing.push('requirements');
  }
} else {
  console.log('requirements.txt file is missing.');
  dependenciesMissing.push('requirements.txt file is missing.');
}

  console.log(dependenciesMissing);
  return dependenciesMissing;
};

const setExecutionPolicy = () => {
  try {
    execSync('Set-ExecutionPolicy Bypass -Scope Process -Force', { shell: 'powershell.exe', stdio: 'inherit' });
    console.log('Execution policy set to Bypass');
  } catch (error) {
    console.error('Failed to set execution policy:', error);
  }
};

const installDependencies = (win, dependencies) => {
  if (dependencies.length === 0) {
    // 설치할 것이 없으면 바로 추가 패키지 설치 호출
    installAdditionalPackages(win, []);
    return;
  }

  const packages = {
    'Node.js': 'nodejs',
    'npm': 'nodejs',
    'Python': 'python',
    'Chocolatey': 'choco'
  };

  // Chocolatey가 목록에 있는 경우 먼저 동기적으로 설치
  if (dependencies.includes('Chocolatey')) {
    try {
      win.webContents.send('install-status', 'Chocolatey 설치 중...');
      const installScript = `
        Set-ExecutionPolicy Bypass -Scope Process -Force;
        [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072;
        iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
      `;
      execSync(installScript, { stdio: 'inherit' });
      win.webContents.send('install-status', 'Chocolatey 설치 완료');
      console.log('Chocolatey 설치 완료');
      dependencies = dependencies.filter(dep => dep !== 'Chocolatey'); // 목록에서 제거
    } catch (error) {
      console.error('Chocolatey 설치에 실패했습니다:', error);
      win.webContents.send('install-status', 'Chocolatey 설치 실패');
      return; // 실패 시 나머지 진행하지 않음
    }
  }

  // 나머지 의존성 동기적으로 설치
  dependencies.forEach(dep => {
    if (packages[dep]) {
      try {
        win.webContents.send('install-status', `${dep} 설치 중...`);
        execSync(`choco install ${packages[dep]} -y`, { stdio: 'inherit' });
        const status = `${dep} 설치 완료`;
        console.log(status);
        win.webContents.send('install-status', status);
      } catch (error) {
        const status = `${dep} 설치 실패: ${error.message}`;
        console.error(status);
        win.webContents.send('install-status', status);
      }
    }
  });

  // Pass win and filtered dependencies to the next function
  const additionalPackages = [];
  if (dependencies.includes('requirements')) additionalPackages.push('requirements');
  if (dependencies.includes('localtunnel')) additionalPackages.push('localtunnel');
  if (dependencies.includes('dotenv')) additionalPackages.push('dotenv');

  console.log(additionalPackages);

  // 모든 설치 완료 후 추가 패키지 설치 호출
  installAdditionalPackages(win, additionalPackages);
};

const installAdditionalPackages = (win, missingDependencies) => {
  let installationsCompleted = 0;
  let totalInstallations = missingDependencies.length; // 설치할 패키지의 개수로 totalInstallations 설정
  
  // 빈 배열인 경우 즉시 완료 처리
  if (totalInstallations === 0) {
    //console.log('설치할 추가 패키지가 없습니다.');
    win.webContents.send('all-installed'); // 바로 완료 메시지를 전송
    return;
  }

  const checkAllInstallationsCompleted = () => {
    if (installationsCompleted === totalInstallations) {
      //console.log('모든 추가 패키지 설치가 완료되었습니다. "all-installed" 신호를 보냅니다.');
      win.webContents.send('all-installed'); // 모든 설치가 완료되었음을 알림
    }
  };

  // 필요한 Python 패키지 설치
  if (missingDependencies.includes('requirements')) {
    if (fs.existsSync('requirements.txt')) {
      win.webContents.send('install-status', 'requirements.txt 설치 중...');
      console.log('requirements.txt에서 Python 패키지 설치 중...');
      exec('pip install -r requirements.txt', (error, stdout, stderr) => {
        if (error) {
          console.error(`Python 패키지 설치 실패: ${error}`);
          win.webContents.send('install-status', `requirements.txt 설치 실패: ${error.message}`);
        } else {
          console.log('requirements.txt에서 Python 패키지 설치 완료.');
          win.webContents.send('install-status', 'requirements.txt 설치 완료');
        }
        installationsCompleted++;
        checkAllInstallationsCompleted(); // 설치 완료 체크
      });
    } else {
      console.log('requirements.txt 파일을 찾을 수 없습니다.');
      win.webContents.send('install-status', 'requirements.txt가 없습니다.');
      installationsCompleted++;
      checkAllInstallationsCompleted(); // 파일이 없을 때도 설치 완료 체크
    }
  }

  // localtunnel 설치
  if (missingDependencies.includes('localtunnel')) {
    win.webContents.send('install-status', 'localtunnel 설치 중...');
    console.log('npm을 사용하여 localtunnel 설치 중...');
    exec('npm install -g localtunnel', (error, stdout, stderr) => {
      if (error) {
        console.error(`localtunnel 설치 실패: ${error}`);
        win.webContents.send('install-status', `localtunnel 설치 실패: ${error.message}`);
      } else {
        console.log('localtunnel 설치 완료.');
        win.webContents.send('install-status', 'localtunnel 설치 완료');
      }
      installationsCompleted++;
      checkAllInstallationsCompleted(); // 설치 완료 체크
    });
  }

  // dotenv 설치
  if (missingDependencies.includes('dotenv')) {
    win.webContents.send('install-status', 'dotenv 설치 중...');
    console.log('npm을 사용하여 dotenv 설치 중...');
    exec('npm install dotenv', (error, stdout, stderr) => {
      if (error) {
        console.error(`dotenv 설치 실패: ${error}`);
        win.webContents.send('install-status', `dotenv 설치 실패: ${error.message}`);
      } else {
        console.log('dotenv 설치 완료.');
        win.webContents.send('install-status', 'dotenv 설치 완료');
        require('dotenv').config();
      }
      installationsCompleted++;
      checkAllInstallationsCompleted(); // 설치 완료 체크
    });
  }
};


const createWindow = () => {
  setExecutionPolicy(); // 처음 실행 시 스크립트 실행 권한 설정
  const missingDependencies = checkDependencies();
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: true,
      contextIsolation: false
    },
  });

  // check_package.html 로드
  win.loadFile('check_package.html');

  // IPC 이벤트 처리: 다음으로 버튼 클릭 시 install.html 로드 및 설치 시작
  ipcMain.on('go-to-install', () => {
    win.loadFile('install.html');

    // install.html이 로드된 후에 설치 시작
    win.webContents.on('did-finish-load', () => {
      installDependencies(win, missingDependencies);
    });
  });

  // IPC 이벤트 처리: 다음으로 버튼 클릭 시 input.html 또는 index.html로 이동
  ipcMain.on('go-to-input-or-index', () => {
    const slackBotToken = process.env.SLACK_BOT_TOKEN;
    const botSubdomain = process.env.BOT_SUBDOMAIN;
    if (slackBotToken && botSubdomain) {
      win.loadFile('index.html'); // 두 환경 변수가 모두 존재하면 index.html 로드
    } else {
      win.loadFile('input.html'); // 둘 중 하나라도 없으면 input.html 로드
    }
  });

  ipcMain.on('request-credentials', (event) => {
    const slackBotToken = process.env.SLACK_BOT_TOKEN || '';
    const botSubdomain = process.env.BOT_SUBDOMAIN || '';
      event.sender.send('load-credentials', { token: slackBotToken, subdomain: botSubdomain });
  });
    
  ipcMain.on('set-credentials', (event, token, subdomain) => {
    const dotenvFilePath = path.join(__dirname, '.env');
    
    // .env 파일 내용 읽기
    let envContent = fs.readFileSync(dotenvFilePath, 'utf-8');

    // 키-값 업데이트 함수
    const updateEnvValue = (content, key, value) => {
        const regex = new RegExp(`^${key}=.*`, 'm'); // 키에 해당하는 라인 검색
        if (regex.test(content)) {
            // 키가 이미 존재하면 값만 업데이트
            return content.replace(regex, `${key}=${value}`);
        } else {
            // 키가 없으면 원본 반환 (추가는 하지 않음)
            return content;
        }
    };

    // SLACK_BOT_TOKEN과 BOT_SUBDOMAIN 값 업데이트
    envContent = updateEnvValue(envContent, 'SLACK_BOT_TOKEN', token);
    envContent = updateEnvValue(envContent, 'BOT_SUBDOMAIN', subdomain);

    // .env 파일에 다시 쓰기
    fs.writeFileSync(dotenvFilePath, envContent, 'utf-8');

    // 환경 변수 즉시 반영
    process.env.SLACK_BOT_TOKEN = token;
    process.env.BOT_SUBDOMAIN = subdomain;

    event.sender.send('credentials-saved');  
  });
    
    ipcMain.on('start-bot', () => {
    // Flask 서버 시작
    if (!flaskProcess) {
        const pythonCommand = 'python'; // Windows에서 python 또는 python3 확인 필요
        const slackScriptPath = path.join(__dirname, 'slack_test.py');
        console.log(__dirname); // 현재 스크립트의 디렉토리 경로가 출력됩니다.
        console.log(slackScriptPath); // slack_test.py에 대한 절대 경로가 출력됩니다.
        flaskProcess = spawn(pythonCommand, [slackScriptPath], { shell: true });

        flaskProcess.stdout.on('data', (data) => {
            console.log(`Flask stdout: ${data}`);
        });

        flaskProcess.stderr.on('data', (data) => {
            console.error(`Flask stderr: ${data}`);
        });

        flaskProcess.on('close', (code) => {
            console.log(`Flask process exited with code ${code}`);
            flaskProcess = null;
        });

        console.log('Flask server started.');
    } else {
        console.log('Flask server is already running.');
    }

    // 로컬터널 시작
    if (!localtunnelProcess) {
        const subdomain = process.env.BOT_SUBDOMAIN || 'default-subdomain';
        localtunnelProcess = spawn('lt', ['--port', '5000', '--subdomain', subdomain], { shell: true });

        localtunnelProcess.stdout.on('data', (data) => {
            console.log(`Localtunnel stdout: ${data}`);
        });

        localtunnelProcess.stderr.on('data', (data) => {
            console.error(`Localtunnel stderr: ${data}`);
        });

        localtunnelProcess.on('close', (code) => {
            console.log(`Localtunnel process exited with code ${code}`);
            localtunnelProcess = null;
        });

        console.log('Localtunnel started.');
    } else {
        console.log('Localtunnel is already running.');
    }
});

  ipcMain.on('stop-bot', () => {
    /*
    // Flask 서버 종료
    if (flaskProcess) {
        console.log('Stopping Flask server...');
        spawn("taskkill", ["/pid", flaskProcess.pid, '/f', '/t']);
        flaskProcess = null;
    } else {
        console.log('No Flask server to stop.');
    }

    // 로컬터널 종료
    if (localtunnelProcess) {
        console.log('Stopping localtunnel...');
        spawn("taskkill", ["/pid", localtunnelProcess.pid, '/f', '/t']);
        localtunnelProcess = null;
    } else {
        console.log('No localtunnel process to stop.');
    }*/
    if (flaskProcess) {
        exec(`taskkill /pid ${flaskProcess.pid} /T /F`, (error, stdout, stderr) => {
            if (error) {
                console.log(`Failed to kill Flask process: ${error}`);
            } else {
                console.log('Flask server stopped.');
                flaskProcess = null;
            }
        });
    }

    if (localtunnelProcess) {
        exec(`taskkill /pid ${localtunnelProcess.pid} /T /F`, (error, stdout, stderr) => {
            if (error) {
                console.log(`Failed to kill Localtunnel process: ${error}`);
            } else {
                console.log('Localtunnel stopped.');
                localtunnelProcess = null;
            }
        });
    }
});
   
  // SIGINT 핸들링 (CTRL+C)
process.on('SIGINT', () => {
    console.log('CTRL+C received. Exiting gracefully...');
    // 필요하면 추가 작업 수행 후 종료
});

  // 누락된 패키지 목록 전송
  win.webContents.on('did-finish-load', () => {
    win.webContents.send('missing-dependencies', missingDependencies);
  });
};

app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

// 앱 종료 시 모든 프로세스 정리
app.on('window-all-closed', () => {
    if (flaskProcess) {
        flaskProcess.kill();
    }
    if (localtunnelProcess) {
        localtunnelProcess.kill();
    }
    if (process.platform !== 'darwin') {
        app.quit();
    }
});
