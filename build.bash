# pip3 install click --target boss

PROJECT_ROOT="$HOME/projects/boss/boss"
BOSS_DIR='boss'

cd $PROJECT_ROOT
if python3 -m zipapp --compress --python "/usr/bin/env python3" $BOSS_DIR; then
    echo 'Boss built'
fi

