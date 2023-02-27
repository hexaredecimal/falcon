
TEST_FOLDER=./tests/
TEST_EXECS=$(TEST_FOLDER)file\
$(TEST_FOLDER)loops\
$(TEST_FOLDER)stars\
$(TEST_FOLDER)factorial\
$(TEST_FOLDER)input\
$(TEST_FOLDER)oop\
$(TEST_FOLDER)match\
$(TEST_FOLDER)cpp\
$(TEST_FOLDER)array

INSTALL_DIR=/usr/bin/
all:
	@printf "\033[92mCompiling \033[93m%s\033[0m\n" "main.c"
	@gcc -Wno-discarded-qualifiers main.c -o falcon
	
test:
	@printf "\033[92mUsing test folder: \033[93m%s\033[0m\n" $(TEST_FOLDER)
	@./tests.sh

clean:
	@printf "\033[92mRemoving executable: \033[93m%s\033[0m\n" "falcon"
	@rm falcon
	@printf "\033[92mRemoving executable: \033[93m%s\033[0m\n" $(TEST_EXECS)
	@rm $(TEST_EXECS)

install:
	@printf "\033[92mCopying files to: \033[93m%s\033[0m\n" $(INSTALL_DIR)
	@cp -rf falcon falconback/ $(INSTALL_DIR)
